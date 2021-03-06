# Foreman and Puppet

This project provides support for automatically provisioning and deploying the sensor code through the use of [The Foreman](https://www.theforeman.org) and [Puppet](https://puppet.com). This documentation does not cover the installation and setup of these tools, and assumes you are familiar with their use.

## Table of Contents

 - [Initial Setup](#initial-setup)
   - [Foreman](#foreman)
   - [Puppet](#puppet)
 - [Creating a New SCOS Sensor](#creating-a-new-scos-sensor)
   - [Host Tab](#host-tab)
   - [Operating System Tab](#operating-system-tab)
   - [Interfaces Tab](#interfaces-tab)
   - [Puppet Classes Tab](#puppet-classes-tab)
   - [Parameters Tab](#parameters-tab)
   - [Additional Information Tab](#additional-information-tab)
 - [Rebuilding an Existing Sensor](#rebuilding-an-existing-sensor)

## Initial Setup

### Foreman

Provisioning is carried out through Foreman. Provisioning bare metal is largely dependent on the hardware, architecture, and distribution you wish to use on the sensor, and is outside the scope of this document. In general, three steps are performed to provision a sensor (which correlates to the three template files needed within Foreman):

* PXE template - Sets up essential OS options (e.g. keyboard layout) and configures DHCP networking
* Provisioning template - Installs selected OS, sets up partition table, and provides configuration options
* Finishing template - Configures Puppet

In Foreman, these are configured through `Hosts > Installation Media`, `Hosts > Provisioning Templates` and `Infrastructure > Provisioning Setup`. To ensure the Puppet 5 agent is installed on the sensors, a `Configure > Global Parameters` parameter was set in Foreman:

`enable-puppetlabs-puppet5-repo = true`

![Puppet 5](/docs/img/foreman_puppet5_parameter.png?raw=true)

### Puppet

The scos-sensor code is deployed through Puppet. Within this scos-sensor repo (in `/scripts`), is a bash script to copy the required `scos` Puppet module to the Puppet Master (a note on nomelcature, Puppet "modules" are synonymous with a Foreman "classes"). Clone this repo to the Puppet Master, and from within the `/scripts` directory run `./puppet_install.sh` and follow the prompts. You should not need to change the defaults. Note, this only needs to be run once.

Once the `scos` Puppet module is installed, you will need to refresh Foreman through the `Configure > Classes > Import Environment from ...` button. You should see a new `scos` class added which needs to be configured before being assigned to a sensor.

The `scos` class has the following parameters which need to be set before it can be assigned to a sensor. Default values have been provided where possible:

* `admin email` - Administrator email address for the sensor API.
* `admin password` - Administrator password for the sensor API. If left blank, the sensor will auto-generate a random 12-digit password, and output it to .admin_password in the install root. It will also be reported as a Puppet fact after the second run.
* `git password` - Github password to use when cloning the scos-sensor repository from Github to the sensor. Only required if using a Github private repository.
* `git username` - Github username to use when cloning the scos-sensor repository from Github to the sensor. Only required if using a Github private repository.
* `install root` - The location on the sensor where the scos-sensor code will be installed.
* `install source` -  Where the scos-sensor code will be sourced from. Either `dockerhub` or `github`. Dockerhub is primarily for production version, Github for development versions.  
* `install version` - A variable pertaining to the branch (Github) or version (Dockerhub) to be installed on the sensor.
* `ssl cert` - The nginx SSL cert to be used on the sensor. You will need to use Foreman `Smart Class Parameter > ssl cert > Matchers` to assign a specific SSL cert to a single host, e.g. by matching on FQDN.
* `ssl dir` - Where the nginx ssl cert will be stored.
* `ssl key` - The private key associated with the nginx ssl cert. You will need to use Foreman `Smart Class Parameter > ssl key > Matchers` to assign a specific private key to a single host. e.g. by matching on FQDN. Make sure this variable has the `Hidden Value` checkbox selected.

![scos class](/docs/img/foreman_scos_class.png?raw=true)

In addition to the `scos` class, the sensors will also need the following classes installed and configured. The names are the modules taken from the [Puppet Forge](https://forge.puppet.com). These can be assigned to a `Configure > Host Group`, to make setup easier:

* [`puppetlabs/docker`](https://forge.puppet.com/puppetlabs/docker)
* [`docker::compose`](https://forge.puppet.com/puppetlabs/docker) - Comes with `puppetlabs/docker` module
* [`puppetlabs/git`](https://forge.puppet.com/puppetlabs/git)
* [`puppetlabs/vcsrepo`](https://forge.puppet.com/puppetlabs/vcsrepo) - Note, this will not show as a Smart Class in Foreman
* [`stankevich/python`](https://forge.puppet.com/stankevich/python)
* `scos` - only do this if you wish to assign it to every sensor in the Host Group

![Host Group](/docs/img/foreman_host_group.png?raw=true)

## Creating a New SCOS Sensor

Once you have Foreman and Puppet setup as above, the procedure for creating a new SCOS sensor is as follows. From within Foreman under `Hosts > Create Host`

### Host Tab

* Name - Sensor hostname. This should match the SSL cert you are assigned to it above.
* Host Group - Select the host group, if you are using this functionality.
* Deploy On - Bare Metal.
* Environment - Select the environment. This needs to match where you installed the SCOS Puppet module.
* Puppet Master - Leave as inherited
* Puppet CA - Leave as inherited

![Host Tab](/docs/img/foreman_host_tab.png?raw=true)

### Operating System Tab

* Architecture - x86_64
* Operating System - Ubuntu 16.04.3 LTS
* Build - Checked
* Media - Ubuntu mirror
* Partition Table - Preseed default
* PXE loader - PXELinux BIOS
* Disk - Leave blank
* Root pass - The system root password you wish to use. **Caution:** as there is no password confirmation box, the suggested procedure is to type the password into a text editor and copy/paste *carefully* into this field.

![Operating System Tab](/docs/img/foreman_os_tab.png?raw=true)

### Interfaces Tab

* Edit the default Interface:
* Type - Interface
* MAC Address - This must match the MAC address of the sensor NIC
* Device Identifier - Not required. Leave blank
* DNS Name - This should match the sensor hostname above
* Domain - Set what Foreman domain this sensor is being deployed to
* IPv4 Subnet - Set what Foreman subnet this sensor is being deployed to
* IPv6 Subnet - No subnets
* IPv4 Address - The IP you want the sensor to have. Must fall within IPv4 subnet
* IPv6 Address - Leave blank
* Managed - Checked
* Primary - Checked
* Provision - Checked
* Virtual NIC - Unchecked

![Interfaces Tab](/docs/img/foreman_interface_tab.png?raw=true)

### Puppet Classes Tab

* See required modules listed above. These can be inherited based on the `Host Group`, if you selected it. If you want to assign the `scos` class at this time, this will install the scos-sensor code automatically, otherwise you'll need to assign it individually to the sensor after provisioning using `Hosts > All Hosts > <sensor name> > Edit > Puppet Classes > +socs`.

![Puppet Classes Tab](/docs/img/foreman_puppet_tab.png?raw=true)

### Parameters Tab

* Leave this section alone, unless you want to make custom changes to the [scos class](./README.md#puppet) operating on this host. I.e.:
* admin_email
* admin_password
* git_username
* git_password
* install-source
* install_version
* ssl_cert
* ssl_key

![Parameters Tab](/docs/img/foreman_parameters_tab.png?raw=true)

### Additional Information Tab

* Owned By - Who should own and manage the host
* Enabled - Checked
* Hardware Model - Leave blank. This will be automatically populated
* Comment - As needed

With all these parameters configured, select the `Submit` button. Foreman is now waiting for the sensor to contact it:  

![Provisioning](/docs/img/foreman_provisioning.png?raw=true)

You will need to go the sensor device and power it on. At startup press `F10` to select boot mode, and from there select `PXE boot`/`Network boot`. If configured correctly the sensor will contact Foreman and start building itself: installing the OS, Puppet, and the scos-sensor code.

## Rebuilding an Existing Sensor

Foreman offers the ability to completely rebuild ("greenfield") a sensor from bare metal using the existing provisioning configuration settings (hostname, MAC, IP, distro etc.). This will re-provision it using PXE, Preseed, and the Puppet configuration, and wipe any and all data on it, so it should be used with caution! **If you are doing this on remote sensors, they need to be configured to "network boot" as default (set in the BIOS of the hardware), or it will not work**.

* Navigate to `Hosts > All Hosts`
* Click on the `name` of the sensor you wish to rebuild
* In the top right, click the `Build` button
* Click the pop-up confirmation `Build` button
* SSH into the sensor and issue the `reboot` command
* The rebuild process will take anywhere from 20-30mins (it is downloading your choosen Linux distro, so it could take a lot longer depending on the speed of your network connection!). Foreman will show the status as "ok" on the sensor host screen when it is rebuilt. You should also start to see Puppet reports flowing in regularly. 

You can also rebuild multiple sensors at once. Select the checkboxes of the appropriate sensors in the `All Hosts` screen, and click the `Select Action` dropdown button in the top right. From the dropdown click `Build`. You will still need to SSH into each sensor to issue the `reboot` command (or alternatively issue the `reboot` command via [Puppet Bolt](https://puppet.com/products/puppet-bolt)).
