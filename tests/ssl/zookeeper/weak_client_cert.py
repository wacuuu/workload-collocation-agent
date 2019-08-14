import wca.security
import wca.databases

ssl = wca.security.SSL()
ssl.server_verify = '/tmp/zk/serverCA.crt'
ssl.client_cert_path = '/tmp/zk/weak.crt'
ssl.client_key_path = '/tmp/zk/weak.key'
zk = wca.databases.ZookeeperDatabase(['localhost:2281'], 'test', ssl=ssl)
zk.set(b'key', b'test')
