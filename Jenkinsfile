pipeline {
     agent any
     environment {
          DOCKERFILES = ''
          JENKINS_HOME = '/var/lib/jenkins'}
          stages{
          stage("Build images") {
              steps {
                  sh '''
                    DOCKERFILES=`cd $JENKINS_HOME/workspace/workloads && find . -name Dockerfile`
                    cd $JENKINS_HOME/workspace/workloads/wrapper
                    echo $USER
                    pwd
                    pipenv install --dev
                    pipenv run tox
                    cd $JENKINS_HOME/workspace/workloads
                    for dockfile in $DOCKERFILES; do docker build -f $dockfile -t `echo $dockfile | cut -d / -f 2` .; done
                  '''         
              }
          }
     }
}
