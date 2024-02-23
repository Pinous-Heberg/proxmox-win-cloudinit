## Manual Patching Instructions

### Qemu.pm
- **File Location:** `/usr/share/perl5/PVE/API2/Qemu.pm`

1. After the line:
   ```perl5
   my $background_delay = extract_param($param, 'background_delay');
   ```
   Add the following code:
   ```perl5
   my $conf = PVE::QemuConfig->load_config($vmid);
   my $ostype = $conf->{ostype};
   ```

2. Delete the following code block:
   ```perl5
   if (defined(my $cipassword = $param->{cipassword})) {
       # Same logic as in cloud-init (but with the regex corrected...)
   ```
   Replace it with:
   ```perl5
   if (!(PVE::QemuServer::windows_version($ostype))) {
       $param->{cipassword} = PVE::Tools::encrypt_pw($cipassword)
           if $cipassword !~ /^\$(? :[156]|2[ay])(\$.+){2}/;
   }
   ```

### Cloudinit.pm
- **File Location:** `/usr/share/perl5/PVE/QemuServer/Cloudinit.pm`

1. After the line:
   ```perl5
   my ($searchdomains, $nameservers) = get_dns_conf($conf);
   ```
   Add:
   ```perl5
   my $ostype = $conf->{"ostype"};
   my $default_dns = '';
   my $default_search = '';
   my $dnsinserted = 0; # insert dns just once for the machine
   ```

2. Add the default DNS after:
   ```perl5
   if ($nameservers && @$nameservers) {
       $nameservers = join(' ', @$nameservers);
       $content .= " dns_nameservers $nameservers\n";
   ```
   Add:
   ```perl5
   $default_dns = $nameservers; # Windows support
   ```

3. Add the following code after:
   ```perl5
   if ($searchdomains && @$searchdomains) {
       $searchdomains = join(' ', @$searchdomains);
       $content .= " dns_search $searchdomains\n";
   ```
   Add:
   ```perl5
   $default_search = $searchdomains; # Windows support
   ```

4. Add the DNS configuration to the network configuration file:
   ```perl5
   if(PVE::QemuServer::windows_version($ostype) && not($dnsinserted)) {
       $content .= " dns-nameservers $default_dns\n";
       $content .= " dns-search $default_search\n";
       $dnsinserted++;
   }
   ```

5. Add the `get_mac_addresses` function after `configdrive2_network`:
   ```perl5
   sub get_mac_addresses {
       # Function code
   }
   ```

6. Replace:
   ```perl5
   my ($user, $network) = @_ ;
   ```
   With:
   ```perl5
   my ($conf, $vmid, $user, $network) = @_ ;
   ```

7. Replace:
   ```perl5
   return configdrive2_metadata($uuid_str) ;
   ```
   With:
   ```perl5
   return configdrive2_metadata($conf, $vmid, $user, $network);
   ```

8. Replace:
   ```perl5
   my ($uuid) = @_;
   ```
   With:
   ```perl5
   my ($password, $uuid, $hostname, $username, $pubkeys, $network, $dhcpmacs) = @_;
   ```

9. Replace:
   ```perl5
   "uuid": "$uuid",
   "network_config": { "content_path": "/content/0000" }
   ```
   With:
   ```perl5
   "meta":{
       "admin_pass": "$password"$username
   },
   "uuid":"$uuid",
   "hostname":"$hostname",
   "network_config":{"content_path":"/content/0000"}$pubkeys$dhcpmacs
   ```

10. Replace:
    ```perl5
    $meta_data = configdrive2_gen_metadata($user_data, $network_data);
    ```
    With:
    ```perl5
    $meta_data = configdrive2_gen_metadata($conf, $vmid, $user_data, $network_data);
    ```
