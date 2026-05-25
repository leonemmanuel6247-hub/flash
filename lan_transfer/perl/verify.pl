use strict;
use warnings;
use Digest::MD5;

sub md5_check {
    my ($file, $expected) = @_;
    my $context = Digest::MD5->new;
    open(my $fh, "<", $file) or die "ERREUR: fichier $file introuvable\n";
    binmode($fh);
    $context->addfile($fh);
    close $fh;
    my $hash = $context->hexdigest;
    if ($hash eq $expected) {
        print "OK: $hash\n";
    } else {
        print "ERREUR: checksum invalide\n";
        print "Attendu: $expected\n";
        print "Obtenu: $hash\n";
        exit 1;
    }
}

if (@ARGV < 2) {
    die "Usage: perl $0 <fichier> <hash>\n";
}

md5_check(@ARGV);
