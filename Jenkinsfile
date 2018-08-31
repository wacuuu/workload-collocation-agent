pipeline {
     agent any
     environment {
          JENKINS_HOME = '/var/lib/jenkins'}
          stages{
          stage("Run tests") {
              steps {
                  sh '''
                    cd $JENKINS_HOME/workspace/rmi
                    pipenv install --dev
                    pipenv run tox
                  '''         
              }
          }
     }
}
