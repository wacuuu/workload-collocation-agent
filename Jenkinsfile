pipeline {
     agent any
     environment {
          JENKINS_HOME = '/var/lib/jenkins'}
          DOCKERFILES = ''
          stages{
          stage("Run tests") {
              steps {
                  sh '''
                    cd $JENKINS_HOME/workspace/owca
                    pipenv install --dev
                    pipenv run tox
                  '''
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
