set -ex
wget https://github.com/centrifugal/centrifugo/releases/download/v1.3.3/centrifugo-1.3.3-linux-amd64.zip
tar -xzvf centrifugo-1.3.3-linux-amd64.zip
sudo mv centrifugo /usr/bin/centrifugo
