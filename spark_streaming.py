from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType
from sklearn.ensemble import IsolationForest
import numpy as np

spark = SparkSession.builder.appName("RealTimeStockDataProcessing").getOrCreate()

ssc = StreamingContext(spark.sparkContext, 10)

kafka_stream = KafkaUtils.createDirectStream(ssc, ['stock-data-topic'], {'metadata.broker.list': 'localhost:9092'})

def isolation_forest_udf(data):
    X = np.array(data)

    model = IsolationForest(contamination=0.05)
    predictions = model.fit_predict(X)

    return predictions.tolist()

isolation_forest_spark_udf = udf(isolation_forest_udf, IntegerType())

def process_rdd(rdd):
    if not rdd.isEmpty():
        df = spark.read.json(rdd)
        
        assembler = VectorAssembler(inputCols=["Open", "High", "Low", "Close"], outputCols="features")
        df = assembler.transform(df)

        df_with_outliers = df.withColumn("outlier", isolation_forest_spark_udf(df['features']))

        df_with_outliers.show()

        df_with_outliers.write \
            .format("org.elasticsearch.spark.sql") \
            .option("es.nodes", "localhost:9200") \
            .option("es.resource", "stock_data/records") \
            .mode("append") \
            .save()
        
kafka_stream.foreachRDD(process_rdd)

ssc.start()
ssc.awaitTermination()