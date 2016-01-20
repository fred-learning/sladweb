__author__ = 'fred_tang'

import subprocess
import  sys

jarpath = " /home/spark/workspace/spark-1.5.2-bin-hadoop2.6/lib/spark-examples-1.5.2-hadoop2.6.0.jar "
jobdict={}
jobdict["org.apache.spark.examples.mllib.MovieLensALS"] = "--rank 4 --numIterations 100 --lambda 1.0 --kryo hdfs:///yateng/mllib/sample_movielens_data.txt"
jobdict["org.apache.spark.examples.mllib.BinaryClassification"]="--algorithm LR --regType L2 --regParam 1.0 --stepSize 1.0 hdfs:///yateng/mllib/sample_binary_classification_data.txt"
jobdict["org.apache.spark.examples.mllib.Correlations"]="--input hdfs:///yateng/mllib/sample_linear_regression_data.txt"
jobdict["org.apache.spark.examples.mllib.LinearRegression"]="hdfs:///yateng/mllib/sample_linear_regression_data.txt"
jobdict["org.apache.spark.examples.mllib.MultivariateSummarizer"]="--input hdfs:///yateng/mllib/sample_linear_regression_data.txt"
jobdict["org.apache.spark.examples.mllib.DenseKMeans"]="--k 10 --numIterations 100 hdfs:///yateng/kmeans_random_data.txt"
jobdict["org.apache.spark.examples.mllib.FPGrowthExample"]="--minSupport 0.5 hdfs:///yateng/mllib/sample_fpgrowth.txt"
jobdict["org.apache.spark.examples.mllib.LDAExample"]="--k 20 hdfs:///yateng/mllib/sample_lda_data.txt"

numexecutors_list = ["9","7","5"]
drivermemory_list=["4g","2g"]
executormemory_list=["4g"]

paramarr = sys.argv
head = paramarr[1]
index = int(paramarr[2])

for numexecutors in numexecutors_list:
    for drivermemory in drivermemory_list:
        for executormemory in executormemory_list:
            for classname in jobdict:
                args = "spark-submit --class " + classname \
                       + " --master yarn-client" \
                       + " --num-executors " + numexecutors \
                       + " --driver-memory " + drivermemory \
                       + " --executor-memory " + executormemory \
                       + jarpath + jobdict[classname]
                print args
                ret = subprocess.call(args,shell=True)
                # no error occur on execute
                if ret == 0:
                    print "Finished!---"+args
                    index = index+1
                    logid = head+str(index)
                    cmd = "yarn logs -applicationId "+logid+">/home/spark/yateng/examplelog/"+logid
                    subprocess.call(cmd,shell=True)
                    print "Finished!---"+cmd
                    raw_input("any key to go on...")
