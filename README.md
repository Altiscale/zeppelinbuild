# zeppelinbuild
Build Script to build Zeppelin application to run on Altiscale

# How to build Zeppelin
The `scripts` directory contains the files that are required to build a RPM.
However, they are not all required.

```
scripts/
├── alti-maven-settings.spec
├── altiscale-zeppelin-centos-6-x86_64.cfg
├── build.sh
├── build_rpm_only.sh
├── install.sh
├── logging.ini
├── setup_env.sh
├── site-defaults.cfg
└── zeppelin.spec
```

To build a RPM in CentOS 6.5, the following files are required.

```
scripts/
├── build_rpm_only.sh
├── setup_env.sh
└── zeppelin.spec
```

- setup_env.sh

This file provides the necessary environment variables that will be part of build_rpm_only.sh and pass
to `zeppelin.spec`. You can use the environment variables here and build Zeppelin without `rpmbuild`.

- zeppelin.spec

This is the required spec file for RPM. If you are building the RPM, this file is required.
You may refer to the mvn command defined in the spec file and simply build Zeppelin.

An example (build with Spark 1.6 and Hadoop 2.7)  may look like this after all the variables are assigned with the proper value.

```
mvn -U -X -Phadoop-2.7 -Pyarn -Pspark-1.6 -Pbuild-distr -Dhadoop.version=2.7.1 -Dyarn.version=2.7.1 -Dhive.version=1.2.1 -Dspark.version=1.6.1 -DskipTests clean package
```

Take a look at the README from https://github.com/apache/incubator-zeppelin 
It provides more detail on how to build Zeppelin and you may cross refer to their settings as well..

- build_rpm_only.sh

The build script that glue things together. It sets the environment variables first by loading `setup_env.sh`
and then replace the variables in the `zeppelin.spec` file, afterward, it will invoke the `rpmbuild` command to 
produce a SRPM first, and then build the real RPM based on the architcture. You will notice there is a maven RPM 
built on the fly, this is not necessary. This maven RPM basically provides the `settings.xml` file for Maven and 
is not required.

The following packages are required to build Zeppelin. Notice apache-maven is not a publically available RPM.
You can simply ignore this and install maven yourself.
```
BuildRequires: apache-maven >= 3.2.1
BuildRequires: jdk >= 1.7.0.51
BuildRequires: npm = 1.3.6
BuildRequires: fontconfig = 2.8.0
```

npm and fontconfig package are required for zeppelin-web module and Phantom JS test cases.

# How to Configure Zeppelin with Altiscale

In order to configure Zeppelin to work with Hive and Spark, you will need to do the following.

1. Copy `/etc/spark/hive-site.xml` to `zeppelin/conf`
2. Copy `/opt/hadoop/share/hadoop/common/lib/hadoop-lzo-*.jar` to `zeppelin/interpreter/spark/`
3. Configure `zeppelin/conf/zeppelin-env.sh`. The following provides an example for Altiscale environment.
```
HADOOP_VERSION=2.7.1
SPARK_VERSION=1.6.1
export SPARK_HOME=/opt/spark/
export SPARK_YARN_JAR=/opt/spark/assembly/target/scala-2.10/spark-assembly-${SPARK_VERSION}-hadoop${HADOOP_VERSION}.jar
export JAVA_HOME=/usr/java/default
export MASTER=yarn-client # Spark master url. eg. spark://master_addr:7077. Leave empty if you want to use local mode.
export ZEPPELIN_JAVA_OPTS="-Dspark.replClassServer.port=45070 -Dspark.executor.memory=2g -Dspark.cores.max=4" 
export HADOOP_CONF_DIR=/etc/hadoop/ # yarn-site.xml is located in configuration directory in HADOOP_CONF_DIR.
export SPARK_SUBMIT_OPTIONS="--jars /opt/hadoop/share/hadoop/common/lib/hadoop-lzo-0.4.18-201507202250.jar"
```
P.S. This changes in Altiscale Spark 1.6.1 since Hive JARs are no longer shaded/embed in the assembly JAR. Take a look at
`/opt/spark/test_spark/test_spark_hql.nokerberos.sh` to see what options are configured and how the Hive JARs are uploaded
to a Spark job.
4. Update some configuration. This is based on Altiscale environment, but you should get the idea.
```
ZEPPELIN_HOME=/opt/zeppelin
rm -rf ${ZEPPELIN_HOME}/logs
mkdir /service/log/zeppelin/
chmod 1777 /service/log/zeppelin 
ln -s /service/log/zeppelin ${ZEPPELIN_HOME}/logs

# and this for temporarily
mkdir -p ${ZEPPELIN_HOME}/run/
chmod 1777 ${ZEPPELIN_HOME}/run/
chmod 1777 ${ZEPPELIN_HOME}/notebook/
```
5. This `interpreter.json` needs to be updateable by the user who is running the Zeppelin daemon.
```
chmod 1777 zeppelin/conf/interpreter.json
```
6. To start Zeppelin
```
cd $ZEPPELIN_HOME
./bin/zeppelin-daemon.sh start
```
