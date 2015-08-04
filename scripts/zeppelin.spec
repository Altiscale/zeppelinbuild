%global apache_name           ZEPPELIN_USER
%global zeppelin_uid          ZEPPELIN_UID
%global zeppelin_gid          ZEPPELIN_GID

%define altiscale_release_ver    ALTISCALE_RELEASE
%define rpm_package_name         alti-zeppelin
%define zeppelin_version         ZEPPELIN_VERSION_REPLACE
%define zeppelin_plain_version   ZEPPELIN_PLAINVERSION_REPLACE
%define current_workspace        CURRENT_WORKSPACE_REPLACE
%define hadoop_version           HADOOP_VERSION_REPLACE
%define hive_version             HIVE_VERSION_REPLACE
%define build_service_name       alti-zeppelin
%define zeppelin_folder_name     %{rpm_package_name}-%{zeppelin_version}
%define zeppelin_testsuite_name  %{zeppelin_folder_name}
%define install_zeppelin_dest    /opt/%{zeppelin_folder_name}
%define install_zeppelin_label   /opt/%{zeppelin_folder_name}/VERSION
%define install_zeppelin_conf    /etc/%{zeppelin_folder_name}
%define install_zeppelin_nb      /opt/%{zeppelin_folder_name}/notebook
%define install_zeppelin_run     /var/run/%{apache_name}
%define install_zeppelin_logs    /var/log/%{apache_name}
# %define install_zeppelin_test    /opt/%{zeppelin_testsuite_name}/test_zeppelin
%define zeppelin_release_dir     /opt/%{apache_name}/lib
%define build_release         BUILD_TIME

Name: %{rpm_package_name}-%{zeppelin_version}
Summary: %{zeppelin_folder_name} RPM Installer AE-1238
Version: %{zeppelin_version}
Release: %{altiscale_release_ver}.%{build_release}%{?dist}
License: ASL 2.0
Group: Development/Libraries
Source: %{_sourcedir}/%{build_service_name}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{release}-root-%{build_service_name}
Requires(pre): shadow-utils
# Requires: scala >= 2.10.4
# Requires: %{rpm_package_name}-%{zeppelin_version}-example
# BuildRequires: vcc-hive-%{hive_version}
# BuildRequires: scala = 2.10.4
BuildRequires: apache-maven >= 3.2.1
BuildRequires: jdk >= 1.7.0.51
# The whole purpose for this req is just to repackage the JAR with JDK 1.6
# BuildRequires: java-1.6.0-openjdk-devel
# For SparkR, prefer R 3.1.2, but we only have 3.1.1
# BuildRequires: vcc-R_3.0.3

Url: https://zeppelin.incubator.apache.org/
%description
Build from https://github.com/Altiscale/zeppelin/tree/branch-0.6.0-alti with 
build script https://github.com/Altiscale/zeppelinbuild/tree/build-0.6.0
Origin source form https://github.com/apache/incubator-zeppelin/tree/master
%{zeppelin_folder_name} is a re-compiled and packaged zeppelin distro that is compiled against Altiscale's 
Hadoop 2.4.x with YARN 2.4.x enabled, and hive-0.13.1a because of Spark. This package should work with Altiscale 
Hadoop 2.4.1 and Hive 0.13.1 (vcc-hadoop-2.4.1 and vcc-hive-0.13.1) and Spark 1.4.1.

%pre
# Soft creation for zeppelin user if it doesn't exist. This behavior is idempotence to Chef deployment.
# Should be harmless. MAKE SURE UID and GID is correct FIRST!!!!!!
# getent group %{apache_name} >/dev/null || groupadd -f -g %{zeppelin_gid} -r %{apache_name}
# if ! getent passwd %{apache_name} >/dev/null ; then
#    if ! getent passwd %{zeppelin_uid} >/dev/null ; then
#      useradd -r -u %{zeppelin_uid} -g %{apache_name} -c "Soft creation of user and group of zeppelin for manual deployment" %{apache_name}
#    else
#      useradd -r -g %{apache_name} -c "Soft adding user zeppelin to group zeppelin for manual deployment" %{apache_name}
#    fi
# fi

%prep
# copying files into BUILD/zeppelin/ e.g. BUILD/zeppelin/* 
# echo "ok - copying files from %{_sourcedir} to folder  %{_builddir}/%{build_service_name}"
# cp -r %{_sourcedir}/%{build_service_name} %{_builddir}/

# %patch1 -p0

%setup -q -n %{build_service_name}

%build
if [ "x${SCALA_HOME}" = "x" ] ; then
  echo "ok - SCALA_HOME not defined, trying to set SCALA_HOME to default location /opt/scala/"
  export SCALA_HOME=/opt/scala/
fi
# AE-1226 temp fix on the R PATH
if [ "x${R_HOME}" = "x" ] ; then
  export R_HOME=$(dirname $(rpm -ql $(rpm -qa | grep vcc-R_.*-0.2.0- | sort -r | head -n 1 ) | grep bin | head -n 1))
  if [ "x${R_HOME}" = "x" ] ; then
    echo "warn - R_HOME not defined, CRAN R isn't installed properly in the current env"
  else
    echo "ok - R_HOME redefined to $R_HOME based on installed RPM due to AE-1226"
    export PATH=$PATH:$R_HOME
  fi
fi

export MAVEN_OPTS="-Xmx2048m -XX:MaxPermSize=1024m"

echo "build - zeppelin core in %{_builddir}"
pushd `pwd`
cd %{_builddir}/%{build_service_name}/

if [ "x%{hadoop_version}" = "x" ] ; then
  echo "fatal - HADOOP_VERSION needs to be set, can't build anything, exiting"
  exit -8
else
  export ZEPPELIN_HADOOP_VERSION=%{hadoop_version}
  echo "ok - applying customized hadoop version $ZEPPELIN_HADOOP_VERSION"
fi
if [ "x%{hive_version}" = "x" ] ; then
  echo "fatal - HIVE_VERSION needs to be set, can't build anything, exiting"
  exit -8
else
  export ZEPPELIN_HIVE_VERSION=%{hive_version}
  echo "ok - applying customized hive version $ZEPPELIN_HIVE_VERSION"
fi

# Always build with YARN
export ZEPPELIN_YARN=true
# Build ZEPPELIN with Hive
export ZEPPELIN_HIVE=true

env | sort

echo "ok - building assembly with HADOOP_VERSION=$ZEPPELIN_HADOOP_VERSION HIVE_VERSION=$ZEPPELIN_HIVE_VERSION ZEPPELIN_YARN=$ZEPPELIN_YARN ZEPPELIN_HIVE=$ZEPPELIN_HIVE"
# ZEPPELIN_HADOOP_VERSION=2.2.0 ZEPPELIN_YARN=true sbt/sbt assembly

# PURGE LOCAL CACHE for clean build
# mvn dependency:purge-local-repository

########################
# BUILD ENTIRE PACKAGE #
########################
# This will build the overall JARs we need in each folder
# and install them locally for further reference. We assume the build
# environment is clean, so we don't need to delete ~/.ivy2 and ~/.m2
# Default JDK version applied is 1.7 here.
if [ -f /etc/alti-maven-settings/settings.xml ] ; then
  echo "ok - applying local maven repo settings.xml for first priority"
  if [[ $ZEPPELIN_HADOOP_VERSION == 2.4.* ]] ; then
    echo "mvn -U -X -Phadoop-2.4 -Pspark-1.4 -Pbuild-distr --settings /etc/alti-maven-settings/settings.xml --global-settings /etc/alti-maven-settings/settings.xml -Dhadoop.version=$ZEPPELIN_HADOOP_VERSION -Dyarn.version=$ZEPPELIN_HADOOP_VERSION -Dhive.version=$ZEPPELIN_HIVE_VERSION -DskipTests clean package"
    mvn -U -X -Phadoop-2.4 -Pspark-1.4 -Pbuild-distr --settings /etc/alti-maven-settings/settings.xml --global-settings /etc/alti-maven-settings/settings.xml -Dhadoop.version=$ZEPPELIN_HADOOP_VERSION -Dyarn.version=$ZEPPELIN_HADOOP_VERSION -Dhive.version=$ZEPPELIN_HIVE_VERSION -DskipTests clean package
  else
    echo "fatal - Unrecognize hadoop version $ZEPPELIN_HADOOP_VERSION, can't continue, exiting, no cleanup"
    exit -9
  fi
else
  echo "ok - applying default repository form pom.xml"
  if [[ $ZEPPELIN_HADOOP_VERSION == 2.4.* ]] ; then
    echo "mvn -U -X -Phadoop-2.4 -Pspark-1.4 -Pbuild-distr -Dhadoop.version=$ZEPPELIN_HADOOP_VERSION -Dyarn.version=$ZEPPELIN_HADOOP_VERSION -Dhive.version=$ZEPPELIN_HIVE_VERSION -DskipTests clean package"
    mvn -U -X -Phadoop-2.4 -Pspark-1.4 -Pbuild-distr -Dhadoop.version=$ZEPPELIN_HADOOP_VERSION -Dyarn.version=$ZEPPELIN_HADOOP_VERSION -Dhive.version=$ZEPPELIN_HIVE_VERSION -DskipTests clean package
  else
    echo "fatal - Unrecognize hadoop version $ZEPPELIN_HADOOP_VERSION, can't continue, exiting, no cleanup"
    exit -9
  fi
fi

popd
echo "ok - build zeppelin core completed successfully!"

%install
# manual cleanup for compatibility, and to be safe if the %clean isn't implemented
rm -rf %{buildroot}%{install_zeppelin_dest}
# re-create installed dest folders
mkdir -p %{buildroot}%{install_zeppelin_dest}
echo "compiled/built folder is (not the same as buildroot) RPM_BUILD_DIR = %{_builddir}"
echo "test installtion folder (aka buildroot) is RPM_BUILD_ROOT = %{buildroot}"
echo "test install zeppelin dest = %{buildroot}/%{install_zeppelin_dest}"
echo "test install zeppelin label zeppelin_folder_name = %{zeppelin_folder_name}"
%{__mkdir} -p %{buildroot}%{install_zeppelin_dest}/
%{__mkdir} -p %{buildroot}/etc/%{install_zeppelin_dest}/
%{__mkdir} -p %{buildroot}%{install_zeppelin_logs}
%{__mkdir} -p %{buildroot}%{install_zeppelin_conf}
%{__mkdir} -p %{buildroot}%{install_zeppelin_nb}
%{__mkdir} -p %{buildroot}%{install_zeppelin_run}
# copy all necessary jars
cp -rp %{_builddir}/%{build_service_name}/* %{buildroot}%{install_zeppelin_dest}/

# test deploy the config folder
cp -rp %{_builddir}/%{build_service_name}/conf %{buildroot}/%{install_zeppelin_conf}

# Inherit license, readme, etc
cp -p %{_builddir}/%{build_service_name}/README.md %{buildroot}/%{install_zeppelin_dest}
cp -p %{_builddir}/%{build_service_name}/LICENSE %{buildroot}/%{install_zeppelin_dest}
cp -p %{_builddir}/%{build_service_name}/NOTICE %{buildroot}/%{install_zeppelin_dest}
cp -p %{_builddir}/%{build_service_name}/DISCLAIMER %{buildroot}/%{install_zeppelin_dest}
# This will capture the installation property form this spec file for further references
rm -f %{buildroot}/%{install_zeppelin_label}
touch %{buildroot}/%{install_zeppelin_label}
echo "name=%{name}" >> %{buildroot}/%{install_zeppelin_label}
echo "version=%{zeppelin_version}" >> %{buildroot}/%{install_zeppelin_label}
echo "release=%{name}-%{release}" >> %{buildroot}/%{install_zeppelin_label}


%clean
echo "ok - cleaning up temporary files, deleting %{buildroot}%{install_zeppelin_dest}"
rm -rf %{buildroot}%{install_zeppelin_dest}

%files
%defattr(0755,zeppelin,zeppelin,0755)
%{install_zeppelin_dest}
%dir %{install_zeppelin_conf}
%attr(0755,root,root) %{install_zeppelin_conf}
%attr(1777,root,root) %{install_zeppelin_logs}
%attr(1777,root,root) %{install_zeppelin_nb}
%attr(1777,root,root) %{install_zeppelin_run}
%config(noreplace) %{install_zeppelin_conf}

%post
if [ "$1" = "1" ]; then
  echo "ok - performing fresh installation"
elif [ "$1" = "2" ]; then
  echo "ok - upgrading system"
fi
rm -vf /opt/%{apache_name}/logs
rm -vf /opt/%{apache_name}/conf
rm -vf /opt/%{apache_name}/test_zeppelin
rm -vf /opt/%{apache_name}
rm -vf /etc/%{apache_name}
ln -vsf %{install_zeppelin_dest} /opt/%{apache_name}
ln -vsf %{install_zeppelin_conf} /etc/%{apache_name}
ln -vsf %{install_zeppelin_conf} /opt/%{apache_name}/conf
ln -vsf %{install_zeppelin_logs} /opt/%{apache_name}/logs
ln -vsf %{install_zeppelin_run} /opt/%{apache_name}/run
# mkdir -p /home/zeppelin/logs
# chmod -R 1777 /home/zeppelin/logs
# chown %{zeppelin_uid}:%{zeppelin_gid} /home/zeppelin/
# chown %{zeppelin_uid}:%{zeppelin_gid} /home/zeppelin/logs


%postun
if [ "$1" = "0" ]; then
  ret=$(rpm -qa | grep %{rpm_package_name} | grep -v test | wc -l)
  if [ "x${ret}" != "x0" ] ; then
    echo "ok - detected other zeppelin version, no need to clean up symbolic links"
    echo "ok - cleaning up version specific directories only regarding this uninstallation"
    rm -vrf %{install_zeppelin_dest}
    rm -vrf %{install_zeppelin_conf}
  else
    echo "ok - uninstalling %{rpm_package_name} on system, removing symbolic links"
    rm -vf /opt/%{apache_name}/logs
    rm -vf /opt/%{apache_name}/conf
    rm -vf /opt/%{apache_name}
    rm -vf /etc/%{apache_name}
    rm -vrf %{install_zeppelin_dest}
    rm -vrf %{install_zeppelin_conf}
  fi
fi
# Don't delete the users after uninstallation.

%changelog
* Tue Aug 4 2015 Andrew Lee 20150804
- Initial Creation of spec file for Apache Zeppelin 0.6.0


