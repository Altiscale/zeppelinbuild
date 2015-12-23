#!/bin/bash

# TBD: honor system pre-defined property/variable files from 
# /etc/hadoop/ and other /etc config for spark, hdfs, hadoop, etc

if [ "x${JAVA_HOME}" = "x" ] ; then
  export JAVA_HOME=/usr/java/default
fi
if [ "x${ANT_HOME}" = "x" ] ; then
  export ANT_HOME=/opt/apache-ant
fi
if [ "x${MAVEN_HOME}" = "x" ] ; then
  export MAVEN_HOME=/opt/apache-maven
fi
if [ "x${M2_HOME}" = "x" ] ; then
  export M2_HOME=/opt/apache-maven
fi
if [ "x${MAVEN_OPTS}" = "x" ] ; then
  export MAVEN_OPTS="-Xmx2g -XX:MaxPermSize=1024M -XX:ReservedCodeCacheSize=512m"
fi
if [ "x${SCALA_HOME}" = "x" ] ; then
  export SCALA_HOME=/opt/scala
fi
if [ "x${HADOOP_VERSION}" = "x" ] ; then
  export HADOOP_VERSION=2.4.1
fi
if [ "x${HIVE_VERSION}" = "x" ] ; then
  export HIVE_VERSION=0.13.1
fi
if [ "x${ALTI_SPARK_VERSION}" = "x" ] ; then
  export ALTI_SPARK_VERSION=1.5.2
fi
# AE-1226 temp fix on the R PATH
if [ "x${R_HOME}" = "x" ] ; then
  export R_HOME=$(dirname $(rpm -ql $(rpm -qa | grep vcc-R_.*-0.2.0- | sort -r | head -n 1 ) | grep bin | head -n 1))
  if [ "x${R_HOME}" = "x" ] ; then
    echo "warn - R_HOME not defined, CRAN R isn't installed properly in the current env"
  else
    echo "ok - R_HOME redefined to $R_HOME based on installed RPM due to AE-1226"
  fi
fi

export PATH=$PATH:$M2_HOME/bin:$SCALA_HOME/bin:$ANT_HOME/bin:$JAVA_HOME/bin:$R_HOME

if [ "x${ZEPPELIN_NAME}" = "x" ] ; then
  export ZEPPELIN_NAME=zeppelin
fi

if [ "x${ZEPPELIN_VERSION}" = "x" ] ; then
  export ZEPPELIN_VERSION=0.6.0
fi
if [ "x${ZEPPELIN_PLAIN_VERSION}" = "x" ] ; then
  export ZEPPELIN_PLAIN_VERSION=0.6.0
fi
if [ "x${ZEPPELIN_YARN}" = "x" ] ; then
  export ZEPPELIN_YARN=true
fi
if [ "x${ZEPPELIN_HIVE}" = "x" ] ; then
  export ZEPPELIN_HIVE=true
fi

if [ "x${HADOOP_VERSION}" = "x2.2.0" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hadoop22"
elif [ "x${HADOOP_VERSION}" = "x2.4.0" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hadoop24"
elif [ "x${HADOOP_VERSION}" = "x2.4.1" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hadoop24"
elif [ "x${HADOOP_VERSION}" = "x2.7.1" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hadoop27"
else
  echo "error - can't recognize altiscale's HADOOP_VERSION=$HADOOP_VERSION"
fi

if [ "x${HIVE_VERSION}" = "x0.12.0" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hive12"
elif [ "x${HIVE_VERSION}" = "x0.13.0" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hive13"
elif [ "x${HIVE_VERSION}" = "x0.13.1" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hive13"
elif [ "x${HIVE_VERSION}" = "x1.2.0" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hive120"
elif [ "x${HIVE_VERSION}" = "x1.2.1" ] ; then
  export ZEPPELIN_VERSION="$ZEPPELIN_VERSION.hive121"
else
  echo "error - can't recognize altiscale's HIVE_VERSION=$HIVE_VERSION"
fi

if [ "x${ALTISCALE_RELEASE}" = "x" ] ; then
  if [ "x${HADOOP_VERSION}" = "x2.2.0" ] ; then
    export ALTISCALE_RELEASE=2.0.0
  elif [ "x${HADOOP_VERSION}" = "x2.4.0" ] ; then
    export ALTISCALE_RELEASE=3.0.0
  elif [ "x${HADOOP_VERSION}" = "x2.4.1" ] ; then
    export ALTISCALE_RELEASE=3.0.0
  elif [ "x${HADOOP_VERSION}" = "x2.7.1" ] ; then
    export ALTISCALE_RELEASE=4.0.0
  else
    echo "error - can't recognize altiscale's HADOOP_VERSION=$HADOOP_VERSION for ALTISCALE_RELEASE"
  fi 
else
  export ALTISCALE_RELEASE
fi 

if [ "x${BRANCH_NAME}" = "x" ] ; then
  export BRANCH_NAME=branch-0.6.0-alti
fi

if [ "x${BUILD_TIMEOUT}" = "x" ] ; then
  export BUILD_TIMEOUT=28400
fi

BUILD_TIME=$(date +%Y%m%d%H%M)
export BUILD_TIME

# Customize build OPTS for MVN
export MAVEN_OPTS="-Xmx2048m -XX:MaxPermSize=1024m"




