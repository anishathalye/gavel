Vagrant.configure(2) do |config|

  config.vm.box = 'debian/jessie64'

  # synced folder
  config.vm.synced_folder '.', '/gavel', type: 'rsync',
    rsync__exclude: ['.git/', 'env/'],
    rsync__args: ['--verbose', '--archive', '-z', '--copy-links']

  # disable default synced folder
  config.vm.synced_folder '.', '/vagrant', disabled: true

  # port forward
  config.vm.network 'forwarded_port', guest: 5000, host: 5000

  # install packages
  config.vm.provision 'shell', inline: <<-EOS
    apt-get -y update

    apt-get install -y \
      postgresql-9.4 postgresql-server-dev-9.4 \
      redis-server \
      python3-dev python3-pip

    pip3 install --upgrade pip
    pip3 install virtualenv
  EOS

  # database setup
  config.vm.provision 'shell', inline: <<-EOS
    pg_auth_file="/etc/postgresql/9.4/main/pg_hba.conf"
    echo "local all   postgres              peer"  >  "$pg_auth_file"
    echo "local all   all                   peer"  >> "$pg_auth_file"
    echo "host  gavel vagrant  ::1/128      trust" >> "$pg_auth_file"
    echo "host  gavel vagrant  127.0.0.1/32 trust" >> "$pg_auth_file"
    service postgresql restart

    su postgres -c "createdb gavel 2>/dev/null || true"

    su postgres -c "createuser vagrant 2>/dev/null || true"
  EOS

end
