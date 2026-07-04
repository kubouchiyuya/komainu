# fixture: path traversal / zip-slip (inert)
import tarfile
tf = tarfile.open("payload.tar")
tf.extractall("/tmp/out")          # zip-slip: no member validation
open("../../etc/evil.conf", "w").write("pwned")
