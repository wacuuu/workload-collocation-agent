pipeline {
     agent any
     environment {
          JENKINS_HOME = '/var/lib/jenkins'
          DOCKERFILES = ''
     }
     stages{
          stage("Run tests") {
              steps {
                  sh '''
                    cd $JENKINS_HOME/workspace/OWCA-production
                    echo "test"
                    pipenv --python /opt/rh/rh-python36/root/bin/python3.6
                    pipenv install --dev
                    pipenv run tox
                  '''
              }
          }
          stage("Build images") {
              steps {
                  sh '''
                    cd $JENKINS_HOME/workspace/OWCA-production/
                    cp $HOME/.kaggle/kaggle.json $JENKINS_HOME/workspace/OWCA-production/workloads/tensorflow-inference/
                    cp $HOME/.kaggle/kaggle.json $JENKINS_HOME/workspace/OWCA-production/workloads/tensorflow-train/
                    mkdir -p $JENKINS_HOME/workspace/OWCA-production/workloads/SpecJBB/specjbb
                    DOCKERFILES=`cd $JENKINS_HOME/workspace/OWCA-production && find . -name Dockerfile`
                    for dockfile in $DOCKERFILES; do docker build -f $dockfile -t `echo $dockfile | cut -d / -f 2 | tr '[:upper:]' '[:lower:]'` .; done
 
                  '''
              }
          }
     }
}
