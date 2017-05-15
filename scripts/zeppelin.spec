%define debug_package %{nil}
%define rpm_package_name      alti-zeppelin
%define build_service_name    alti-zeppelin
%define zeppelin_folder_name     %{rpm_package_name}-%{_zeppelin_version}
%define zeppelin_testsuite_name  %{zeppelin_folder_name}
%define install_zeppelin_dest    /opt/%{zeppelin_folder_name}
%define zeppelin_bin_dir     /opt/%{zeppelin_folder_name}/bin
%define zeppelin_release_dir     /opt/%{zeppelin_folder_name}/lib
%define install_zeppelin_nb      /opt/%{zeppelin_folder_name}/notebook
%define zeppelin_license_dir     /opt/%{zeppelin_folder_name}/licenses
%define install_zeppelin_label   /opt/%{zeppelin_folder_name}/VERSION
%define install_zeppelin_conf    /etc/%{zeppelin_folder_name}
%define install_zeppelin_run     /var/run/%{_apache_name}
%define install_zeppelin_logs    /service/log/%{_apache_name}

Name: %{rpm_package_name}-%{_zeppelin_version}
Summary: %{zeppelin_folder_name} RPM Installer AE-576, cluster mode restricted with warnings
Version: %{_zeppelin_version}
Release: %{_altiscale_release_ver}.%{_build_release}%{?dist}
License: Apache Software License 2.0
Group: Development/Libraries
Source: %{_sourcedir}/%{build_service_name}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{release}-root-%{build_service_name}
Requires(pre): shadow-utils
Requires: scala = 2.10.5
# BuildRequires: vcc-hive-%{_hive_version}
BuildRequires: scala = 2.10.5
BuildRequires: apache-maven >= 3.3.3
BuildRequires: jdk >= 1.7.0.51
BuildRequires: git >= 1.7.1

Url: http://zeppelin.apache.org/
%description
Build from https://github.com/Altiscale/zeppelin/tree/branch-0.6-alti with 
build script https://github.com/Altiscale/zeppelinbuild/tree/branch-0.6-alti
Origin source form https://github.com/apache/zeppelin/tree/branch-0.6
%{zeppelin_folder_name} is a re-compiled and packaged zeppelin distro that is compiled against Altiscale's 
Hadoop 2.7.x with YARN 2.7.x enabled, spark 1.6.x, and hive-1.2.1. This package should work with Altiscale 
Hadoop 2.7.x, Spark 1.6.x, and Hive 1.2.1 (alti-hadoop-2.7.x, alti-spark-1.6.x, and alti-hive-1.2.x).

%pre

%prep

%setup -q -n %{build_service_name}

%build
if [ "x${SCALA_HOME}" = "x" ] ; then
  echo "ok - SCALA_HOME not defined, trying to set SCALA_HOME to default location /opt/scala/"
  export SCALA_HOME=/opt/scala/
fi
# AE-1226 temp fix on the R PATH
if [ "x${R_HOME}" = "x" ] ; then
  export R_HOME=$(dirname $(dirname $(rpm -ql $(rpm -qa | grep vcc-R_.*-0.2.0- | sort -r | head -n 1 ) | grep bin | head -n 1)))
  if [ "x${R_HOME}" = "x" ] ; then
    echo "warn - R_HOME not defined, CRAN R isn't installed properly in the current env"
  else
    echo "ok - R_HOME redefined to $R_HOME based on installed RPM due to AE-1226"
    export PATH=$PATH:$R_HOME
  fi
fi
if [ "x${JAVA_HOME}" = "x" ] ; then
  export JAVA_HOME=/usr/java/default
  # Hijack JAva path to use our JDK 1.7 here instead of openjdk
  export PATH=$JAVA_HOME/bin:$PATH
fi
export MAVEN_OPTS="-Xmx2048m -XX:MaxPermSize=1024m"

echo "build - entire zeppelin project in %{_builddir}"
pushd `pwd`
cd %{_builddir}/%{build_service_name}/

# clean up for *NIX environment only, deleting window's cmd
find %{_builddir}/%{build_service_name}/bin -type f -name '*.cmd' -exec rm -f {} \;

if [ "x%{_hadoop_version}" = "x" ] ; then
  echo "fatal - HADOOP_VERSION needs to be set, can't build anything, exiting"
  exit -8
else
  export SPARK_HADOOP_VERSION=%{_hadoop_version}
  echo "ok - applying customized hadoop version $SPARK_HADOOP_VERSION"
fi

if [ "x%{_hive_version}" = "x" ] ; then
  echo "fatal - HIVE_VERSION needs to be set, can't build anything, exiting"
  exit -8
else
  export SPARK_HIVE_VERSION=%{_hive_version}
  echo "ok - applying customized hive version $SPARK_HIVE_VERSION"
fi

env | sort

echo "ok - building Apache zeppelin with HADOOP_VERSION=$SPARK_HADOOP_VERSION HIVE_VERSION=$SPARK_HIVE_VERSION scala=scala-%{_scala_build_version}"

# PURGE LOCAL CACHE for clean build
# mvn dependency:purge-local-repository

########################
# BUILD ENTIRE PACKAGE #
########################
# This will build the overall JARs we need in each folder
# and install them locally for further reference. We assume the build
# environment is clean, so we don't need to delete ~/.ivy2 and ~/.m2
# Default JDK version applied is 1.7 here.

# hadoop.version, yarn.version, and hive.version are all defined in maven profile now
# they are tied to each profile.
# hadoop-2.2 No longer supported, removed.
# hadoop-2.4 hadoop.version=2.4.1 yarn.version=2.4.1 hive.version=0.13.1a hive.short.version=0.13.1
# hadoop-2.6 hadoop.version=2.6.0 yarn.version=2.6.0 hive.version=1.2.1.zeppelin hive.short.version=1.2.1
# hadoop-2.7 hadoop.version=2.7.1 yarn.version=2.7.1 hive.version=1.2.1.zeppelin hive.short.version=1.2.1

hadoop_profile_str=""
testcase_hadoop_profile_str=""
if [[ %{_hadoop_version} == 2.4.* ]] ; then
  hadoop_profile_str="-Phadoop-2.4"
  testcase_hadoop_profile_str="-Phadoop24-provided"
elif [[ %{_hadoop_version} == 2.6.* ]] ; then
  hadoop_profile_str="-Phadoop-2.6"
  testcase_hadoop_profile_str="-Phadoop26-provided"
elif [[ %{_hadoop_version} == 2.7.* ]] ; then
  hadoop_profile_str="-Phadoop-2.7"
  testcase_hadoop_profile_str="-Phadoop27-provided"
else
  echo "fatal - Unrecognize hadoop version %{_hadoop_version}, can't continue, exiting, no cleanup"
  exit -9
fi
xml_setting_str=""

if [ -f %{_mvn_settings} ] ; then
  echo "ok - picking up %{_mvn_settings}"
  xml_setting_str="--settings %{_mvn_settings} --global-settings %{_mvn_settings}"
elif [ -f %{_builddir}/.m2/settings.xml ] ; then
  echo "ok - picking up %{_builddir}/.m2/settings.xml"
  xml_setting_str="--settings %{_builddir}/.m2/settings.xml --global-settings %{_builddir}/.m2/settings.xml"
elif [ -f /etc/alti-maven-settings/settings.xml ] ; then
  echo "ok - applying local installed maven repo settings.xml for first priority"
  xml_setting_str="--settings /etc/alti-maven-settings/settings.xml --global-settings /etc/alti-maven-settings/settings.xml"
else
  echo "ok - applying default repository from pom.xml"
  xml_setting_str=""
fi

# TODO: This needs to align with Maven settings.xml, however, Maven looks for
# -SNAPSHOT in pom.xml to determine which repo to use. This creates a chain reaction on 
# legacy pom.xml design on other application since they are not implemented in the Maven way.
# :-( 
# Will need to create a work around with different repo URL and use profile Id to activate them accordingly
# mvn_release_flag=""
# if [ "x%{_production_release}" == "xtrue" ] ; then
#   mvn_release_flag="-Preleases"
# else
#   mvn_release_flag="-Psnapshots"
# fi

mvn_cmd="mvn -U -X $hadoop_profile_str -Pscala-%{_scala_build_version} -Pyarn -Ppyspark -Psparkr -Pspark-%{_spark_version} $xml_setting_str -Dspark.version=%{_spark_minor_version} -Dhadoop.version=%{_hadoop_version} -Dyarn.version=%{_hadoop_version} -Dhive.version=%{_hive_version} -DskipTests clean package"
echo "$mvn_cmd"
$mvn_cmd

popd
echo "ok - build zeppelin project completed successfully!"

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
%{__mkdir} -p %{buildroot}%{zeppelin_release_dir}
%{__mkdir} -p %{buildroot}%{zeppelin_license_dir}
%{__mkdir} -p %{buildroot}%{zeppelin_bin_dir}

# copy all necessary jars
cp -p %{_builddir}/%{build_service_name}/zeppelin-web/target/zeppelin-web-%{_zeppelin_version}.war %{buildroot}%{install_zeppelin_dest}/
cp -p %{_builddir}/%{build_service_name}/zeppelin-server/target/zeppelin-server-%{_zeppelin_version}.jar %{buildroot}%{install_zeppelin_dest}/
cp -p %{_builddir}/%{build_service_name}/zeppelin-interpreter/target/zeppelin-interpreter-%{_zeppelin_version}.jar %{buildroot}%{zeppelin_release_dir}/
cp -p %{_builddir}/%{build_service_name}/zeppelin-zengine/target/zeppelin-zengine-%{_zeppelin_version}.jar %{buildroot}%{zeppelin_release_dir}/

# provide auxiliaries JARs
cp -p %{_builddir}/%{build_service_name}/zeppelin-interpreter/target/lib/* %{buildroot}%{zeppelin_release_dir}/
cp -p %{_builddir}/%{build_service_name}/zeppelin-zengine/target/lib/* %{buildroot}%{zeppelin_release_dir}/
cp -p %{_builddir}/%{build_service_name}/zeppelin-server/target/lib/* %{buildroot}%{zeppelin_release_dir}/
cp -p %{_builddir}/%{build_service_name}/zeppelin-server/target/lib/* %{buildroot}%{zeppelin_release_dir}/


cp -rp %{_builddir}/%{build_service_name}/interpreter %{buildroot}%{install_zeppelin_dest}/
cp -rp %{_builddir}/%{build_service_name}/notebook/* %{buildroot}%{install_zeppelin_nb}/
cp -rp %{_builddir}/%{build_service_name}/bin/* %{buildroot}%{zeppelin_bin_dir}/

# test deploy the config folder
cp -rp %{_builddir}/%{build_service_name}/conf/* %{buildroot}/%{install_zeppelin_conf}

# Inherit license, readme, etc
cp -p %{_builddir}/%{build_service_name}/README.md %{buildroot}/%{install_zeppelin_dest}
cp -p %{_builddir}/%{build_service_name}/LICENSE %{buildroot}/%{install_zeppelin_dest}
cp -p %{_builddir}/%{build_service_name}/NOTICE %{buildroot}/%{install_zeppelin_dest}
cp -p %{_builddir}/%{build_service_name}/zeppelin-distribution/src/bin_license/licenses/* %{buildroot}/%{zeppelin_license_dir}

# This will capture the installation property form this spec file for further references
rm -f %{buildroot}/%{install_zeppelin_label}
touch %{buildroot}/%{install_zeppelin_label}
echo "name=%{name}" >> %{buildroot}/%{install_zeppelin_label}
echo "version=%{_zeppelin_version}" >> %{buildroot}/%{install_zeppelin_label}
echo "release=%{name}-%{release}" >> %{buildroot}/%{install_zeppelin_label}
echo "git_rev=%{_git_hash_release}" >> %{buildroot}/%{install_zeppelin_label}

%clean
echo "ok - cleaning up temporary files, deleting %{buildroot}%{install_zeppelin_dest}"
rm -rf %{buildroot}%{install_zeppelin_dest}

%files
%defattr(0755,root,root,0755)
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
# TODO: Move to Chef later. The symbolic link is version sensitive
# CLean up old symlink
rm -vrf %{install_zeppelin_dest}/logs
rm -vrf %{install_zeppelin_dest}/conf
# Restore conf and logs symlink
ln -vsf %{install_zeppelin_conf} %{install_zeppelin_dest}/conf
ln -vsf %{install_zeppelin_logs} %{install_zeppelin_dest}/logs

%postun
if [ "$1" = "0" ]; then
  ret=$(rpm -qa | grep %{rpm_package_name} | grep -v example | wc -l)
  # The rpm is already uninstall and shouldn't appear in the counts
  if [ "x${ret}" != "x0" ] ; then
    echo "ok - detected other zeppelin version, no need to clean up symbolic links"
    echo "ok - cleaning up version specific directories only regarding this uninstallation"
    rm -vrf %{install_zeppelin_dest}
    rm -vrf %{install_zeppelin_conf}
  else
    echo "ok - uninstalling %{rpm_package_name} on system, removing symbolic links"
    rm -vf %{install_zeppelin_dest}/logs
    rm -vf %{install_zeppelin_dest}/conf
    rm -vrf %{install_zeppelin_dest}
    rm -vrf %{install_zeppelin_conf}
  fi
fi

%changelog
* Sun Dec 4 2016 Andrew Lee 20161204
- Update spec to align with new build script and spark 2.0.2
* Fri Nov 20 2015 Andrew Lee 20151120
- Support multiple version of spark and hadoop
* Sat Nov 14 2015 Andrew Lee 20151114
- Initial Creation of spec file for Apache Zeppelin 0.5.5
* Tue Aug 4 2015 Andrew Lee 20150804
- Initial Creation of spec file for Apache Zeppelin 0.6.0
