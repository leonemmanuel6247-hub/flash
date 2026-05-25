use strict;
use warnings;
use File::Copy;
use Getopt::Long;
use POSIX qw(strftime);

my $dir = '.';
GetOptions("dir=s" => \$dir);
$dir = shift @ARGV if @ARGV;

opendir(my $dh, $dir) or die "ERREUR: dossier $dir introuvable\n";
my @files = readdir $dh;
closedir $dh;

foreach my $file (@files) {
    next if $file =~ /^\./;
    my $newname = $file;
    $newname =~ s/\s+/_/g;
    # On garde les caracteres alphanumeriques, points, tirets et underscores
    $newname =~ s/[^a-zA-Z0-9._-]//g;
    # Ajout de la date avant l'extension
    my $date = strftime("%Y%m%d", localtime);
    $newname =~ s/(\.[^.]+)$/_$date$1/;
    
    if ($newname ne $file) {
        my $src = "$dir/$file";
        my $dst = "$dir/$newname";
        move($src, $dst) or warn "ERREUR: $file -> $newname : $!\n";
        print "$file -> $newname\n";
    }
}
