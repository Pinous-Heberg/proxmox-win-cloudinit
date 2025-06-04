package PVE::QemuServer::PasswordUtils;

use strict;
use warnings;

use MIME::Base64 qw(encode_base64 decode_base64);
use Digest::SHA qw(sha256);

# Generate a unique encryption key for each VM
sub _generate_vm_key {
    my ($vmid) = @_;
    
    # Use VM ID, hostname, and a secret salt to generate unique key
    my $hostname = `hostname` || 'proxmox';
    chomp $hostname;
    my $salt = 'proxmox-win-cloudinit-v2.0';
    my $key_material = "$vmid:$hostname:$salt";
    
    return substr(sha256($key_material), 0, 24); # Use first 24 bytes for better security
}

sub encrypt_pw_reversible {
    my ($password, $vmid) = @_;
    
    return $password if !defined($password) || $password eq '';
    return $password if $password =~ /^\$5\$/; # Already encrypted in new format
    
    # Default vmid if not provided (for backward compatibility)
    $vmid = 'default' if !defined($vmid);
    
    my $result = eval {
        my $encryption_key = _generate_vm_key($vmid);
        
        # Simple XOR encryption with VM-specific key
        my $encrypted = '';
        my $key_len = length($encryption_key);
        for my $i (0 .. length($password) - 1) {
            my $char = substr($password, $i, 1);
            my $key_char = substr($encryption_key, $i % $key_len, 1);
            $encrypted .= chr(ord($char) ^ ord($key_char));
        }
        
        my $encoded = encode_base64($encrypted, '');
        # Format like a standard crypt hash but with our encrypted data hidden in the middle
        my $salt = sprintf("%08x", $vmid);  # Use vmid as visible salt
        return "\$5\$$salt\$${encoded}Ax4D22Lzejo";
    };
    
    if ($@) {
        warn "Failed to encrypt password: $@";
        return $password; # Return original password on error
    }
    
    return $result;
}

sub decrypt_pw_reversible {
    my ($encrypted_password, $vmid) = @_;
    
    return $encrypted_password if !defined($encrypted_password) || $encrypted_password eq '';
    
    # Default vmid if not provided (for backward compatibility)
    $vmid = 'default' if !defined($vmid);
    
    # Check for new format $5$salt$encrypteddata
    if ($encrypted_password =~ /^\$5\$([0-9a-f]+)\$(.+)Ax4D22Lzejo$/) {
        my ($salt, $encoded_data) = ($1, $2);
        my $expected_vmid = hex($salt);
        
        # Verify the salt matches the vmid
        if ($expected_vmid != $vmid) {
            warn "VMID mismatch in encrypted password: expected $vmid, got $expected_vmid";
            return $encrypted_password;
        }
        
        my $result = eval {
            my $encryption_key = _generate_vm_key($vmid);
            my $encrypted = decode_base64($encoded_data);
            
            # Simple XOR decryption with VM-specific key
            my $decrypted = '';
            my $key_len = length($encryption_key);
            for my $i (0 .. length($encrypted) - 1) {
                my $char = substr($encrypted, $i, 1);
                my $key_char = substr($encryption_key, $i % $key_len, 1);
                $decrypted .= chr(ord($char) ^ ord($key_char));
            }
            
            return $decrypted;
        };
        
        if ($@) {
            warn "Failed to decrypt password: $@";
            return $encrypted_password;
        }
        
        return $result;
    }
    
    return $encrypted_password if $encrypted_password !~ /^\$5\$/; # Not encrypted in legacy format

    my $encoded_data = $encrypted_password;
    $encoded_data =~ s/^\$5\$//;

    my $result = eval {
        my $encryption_key = _generate_vm_key($vmid);
        my $encrypted = decode_base64($encoded_data);
        
        # Simple XOR decryption with VM-specific key
        my $decrypted = '';
        my $key_len = length($encryption_key);
        for my $i (0 .. length($encrypted) - 1) {
            my $char = substr($encrypted, $i, 1);
            my $key_char = substr($encryption_key, $i % $key_len, 1);
            $decrypted .= chr(ord($char) ^ ord($key_char));
        }
        
        return $decrypted;
    };
    
    if ($@) {
        warn "Failed to decrypt password: $@";
        return $encrypted_password; # Return encrypted password on error
    }
    
    return $result;
}

# Export the VM-specific key for use in meta_data (for debugging/testing purposes)
sub get_vm_key {
    my ($vmid) = @_;
    return _generate_vm_key($vmid);
}

1;
