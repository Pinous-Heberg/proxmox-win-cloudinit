Proceed as follows to apply the patches manually;

There are two files we need to modify;

## Qemu.pm
At: /usr/share/perl5/PVE/API2/Qemu.pm

We need to change the user's password to plain text because it's hashed by default and Cloudbase-Init can't use it as it is.
We can get the operating system type from the VM options, so we'll use that to prevent Proxmox from hashing it if it's a Windows VM.

we need to add the following code after 
```perl5
my $background_delay = extract_param($param, 'background_delay') ;

```

code to add :
```perl5
my $conf = PVE::QemuConfig->load_config($vmid) ;

my $ostype = $conf->{ostype} ;

```

then we need to delete the code below after this code:

```perl5
     if (defined(my $cipassword = $param->{cipassword})) {
 	# Same logic as in cloud-init (but with the regex corrected...)
```

code to be deleted:

```perl5
$param->{password} = PVE::Tools::encrypt_pw($password)
if $cipassword !~ /^\$(? :[156]|2[ay])(\$.+){2}/ ;
```
and add this one to check if the operating system type is set to Windows :

```perl5
if (!(PVE::QemuServer::windows_version($ostype))) {
		$param->{cipassword} = PVE::Tools::encrypt_pw($cipassword)
			if $cipassword !~ /^\$(? :[156]|2[ay])(\$.+){2}/ ;
	}
```

## Cloudinit.pm
At: /usr/share/perl5/PVE/QemuServer/Cloudinit.pm

We need to make a few changes to generate a meta_data.json compatible with Cloudbase-Init.

We delete and add a few lines to add the DNS configuration after these lines:

```perl5
     my $content = "auto lo\n";
     $content .= "iface lo inet loopback\n";
```

code to be deleted:

```perl5
my ($searchdomains, $nameservers) = get_dns_conf($conf);
```

code to add:

```perl5
 my ($searchdomains, $nameservers) = get_dns_conf($conf); 

	## support windows
	my $ostype = $conf->{"ostype"};
	my $default_dns = '';
	my $default_search = '';
	##
	my $dnsinserted = 0; # insert dns just once for the machine

```

now we are going to add the default DNS to do this we must add the following code after it

```perl5
if ($nameservers && @$nameservers) {
 	$nameservers = join(' ', @$nameservers);
 	$content .= " dns_nameservers $nameservers\n";
```

code to add :

```perl5
	$default_dns = $nameservers; # Windows support
```

we do the same here :

```perl5
if ($searchdomains && @$searchdomains) {
 	$searchdomains = join(' ', @$searchdomains);
 	$content .= " dns_search $searchdomains\n";
```

code to add :

```perl5
$default_search = $searchdomains; # Windows support
```

we are now going to add this code which allows to add the dns in the configuration file of the network in order to be able to set them at startup

add the code after these lines :

```perl5
    my @ifaces = grep { /^net(\d+)$/ } keys %$conf;
 		$content .= " address $addr\n";
 		$content .= " netmask $mask\n";
 		$content .= " gateway $net->{gw}\n" if $net->{gw};
```

code to add :

```perl5
		## Windows support
		if(PVE::QemuServer::windows_version($ostype) && not($dnsinserted)) {
		    $content .= " dns-nameservers $default_dns\n";
		    $content .= " dns-search $default_search\n";
		    $dnsinserted++;
		}
		##
```

now we're going to add the function that retrieves the MAC address of the network card for DHCP after the configdrive2_network function

code to add:

```perl5

# Get mac addresses of dhcp nics from conf file
sub get_mac_addresses {
     my ($conf) = @_;
     
     my $dhcpstring = undef;
     my @dhcpmacs = ();
     my @ifaces = grep { /^net(\d+)$/ } keys %$conf;
     
     foreach my $iface (sort @ifaces) {
         (my $id = $iface) =~ s/^net//;
         my $net = PVE::QemuServer::parse_net($conf->{$iface});
         next if !$conf->{"ipconfig$id"};
         my $ipconfig = PVE::QemuServer::parse_ipconfig($conf->{"ipconfig$id"});
         
         my $mac = lc $net->{macaddr};

         if (($ipconfig->{ip}) and ($ipconfig->{ip} eq 'dhcp')){
             push @dhcpmacs, $mac;
         }
     }

     if (@dhcpmacs){
         $dhcpstring = ",\n     \"dhcp\":[";
         foreach my $mac (@dhcpmacs){
             if ($mac != $dhcpmacs[-1]){
                 $dhcpstring .= "\"$mac\",";
             }
             else{
                 $dhcpstring .= "\"$mac\"]";
             }
         }
     }
     return ($dhcpstring);
}

```

Now we're going to delete and add some lines in the configdrive2_gen_metadata function. First of all, we're going to replace this line:

```perl5
my ($user, $network) = @_ ;
```
with these lines

```perl5
    my ($conf, $vmid, $user, $network) = @_ ;
 
	# Get the mac addresses of the dhcp nics from the conf file  
	my $dhcpmacs = undef ;
	$dhcpmacs = get_mac_addresses($conf) ;

	# Get the UUID
```

then we replace this line :

```perl5
return configdrive2_metadata($uuid_str) ;
```

with these lines:

```perl5

	# Get the hostname
	my ($hostname, $fqdn) = get_hostname_fqdn($conf, $vmid) ;

	# Obtain the user name, by default Administrator if there is none
	my $username = undef ;
	if (defined($conf->{ciuser})){
        my $name = $conf->{ciuser} ;
        $username = ",\N-"admin_username" : \N- "$name\N""
    }

	# Obtain the user's password
	my $password = $conf->{cipassword} ;

	# Retrieve the ssh keys and list them in json format
	my $keystring = undef ;
	my $pubkeys = $conf->{sshkeys} ;
	$pubkeys = URI::Escape::uri_unescape($pubkeys) ;
	my @pubkeysarray = split "\n", $pubkeys ;
    if (@pubkeysarray) {
        my $arraylength = @pubkeysarray ;
        my $incrementer = 1 ;
        $keystring =",\n "public_keys" : {\n" ;
        for my $key (@pubkeysarray){
            $keystring .= " \"SSH${incrementer}\" : \N- "${key}\N"" ;
            if ($arraylength != $incrementer){
                $keystring .= ",\n" ;
            }else{
                $keystring .= "\n }" ;
            }
            $incrementer ;
        }
    }

    return configdrive2_metadata($password, $uuid_str, $hostname, $username, $keystring, $network, $dhcpmacs) ;
```

then we need to replace this

with these lines:

```perl5


	# Get the hostname
	my ($hostname, $fqdn) = get_hostname_fqdn($conf, $vmid) ;

	# Obtain the user name, by default Administrator if there is none
	my $username = undef ;
	if (defined($conf->{ciuser})){
        my $name = $conf->{ciuser} ;
        $username = ",\N-"admin_username" : \N- "$name\N""
    }

	# Obtain the user's password
	my $password = $conf->{cipassword} ;

	# Retrieve the ssh keys and list them in json format
	my $keystring = undef ;
	my $pubkeys = $conf->{sshkeys} ;
	$pubkeys = URI::Escape::uri_unescape($pubkeys) ;
	my @pubkeysarray = split "\n", $pubkeys ;
    if (@pubkeysarray) {
        my $arraylength = @pubkeysarray ;
        my $incrementer = 1 ;
        $keystring =",\n "public_keys" : {\n" ;
        for my $key (@pubkeysarray){
            $keystring .= " \"SSH${incrementer}\" : \N- "${key}\N"" ;
            if ($arraylength != $incrementer){
                $keystring .= ",\n" ;
            }else{
                $keystring .= "\n }" ;
            }
            $incrementer ;
        }
    }

    return configdrive2_metadata($password, $uuid_str, $hostname, $username, $keystring, $network, $dhcpmacs) ;
```

then we need to replace a few lines in the configdrive2_metadata function the first line to be replaced is the following:

```perl5
my ($uuid) = @_;
```

with this line:

```perl5
my ($password, $uuid, $hostname, $username, $pubkeys, $network, $dhcpmacs) = @_;
```

then we need to replace these two lines:

```perl5
"uuid": "$uuid",
"network_config": { "content_path": "/content/0000" }
```

with these lines:

```perl5
"meta":{
        "admin_pass": "$password"$username
     },
     "uuid":"$uuid",
     "hostname":"$hostname",
     "network_config":{"content_path":"/content/0000"}$pubkeys$dhcpmacs
```

and finally we need to replace this line

```perl5
$meta_data = configdrive2_gen_metadata($user_data, $network_data);
```

with this line:

```perl5
$meta_data = configdrive2_gen_metadata($conf, $vmid, $user_data, $network_data);
```
