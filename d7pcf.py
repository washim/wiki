import os
import shlex, subprocess
from shutil import copy,copytree
class d7pcf:
    def __init__(self):
        self.root = raw_input("Drupal root folder absolute path: ");
        self.name = raw_input("PCF Apps Name: ");
        self.mysql = raw_input("MySQL Service: ");
        self.mysqlcups = raw_input("MySQL CUPS Service: ");
        self.sso = raw_input("SSO Service: ");
        self.s3fs = raw_input("S3fs Service: ");
        self.redis = raw_input("Redis Cache Service: ");
        self.memcache = raw_input("Memcache Service: ");
        self.varnish = raw_input("Varnish Service: ");
        self.modules = 'sites/all/modules/'
        self.services = self.services()
        self.copy()
        self.manifest()
        self.replace_line(self.root + '.htaccess', 6, '  Require all granted\n')
        self.settingsphp()
        self.install()
    def install(self):
        del os.environ['http_proxy']
        del os.environ['https_proxy']
        command_line = "cf push " + self.name + " -f " + self.root
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout = subprocess.PIPE, bufsize = 1)
        for line in iter(p.stdout.readline, b''):
            print line,
        p.stdout.close()
        p.wait()
    def manifest(self):
        if os.path.exists(self.root + 'manifest.yml') == False:
            copy('manifest.yml', self.root + 'manifest.yml')
        lines = open(self.root + 'manifest.yml', 'r').readlines()
        key = 0
        for text in lines:
            if text == '    env:\n':
                break
            else:
                key += 1
        if key > 10:
            del lines[10:key]
        lines[4] = '  - name: ' + self.name + '\n'
        lines[5] = '    host: ' + self.name + '\n'
        lines[9] = self.services
        out = open(self.root + 'manifest.yml', 'w')
        out.writelines(lines)
        out.close()
    def replace_line(self, filename, filenumber, text):
        lines = open(filename, 'r').readlines()
        lines[filenumber] = text
        out = open(filename, 'w')
        out.writelines(lines)
        out.close()
    def settingsphp(self):
        if os.path.exists(self.root + 'sites/default/pcf.php') == False:
            copy('pcf.php', self.root + 'sites/default/pcf.php')
        if os.path.exists(self.root + 'sites/default/settings.php') == False:
            copy(self.root + 'sites/default/default.settings.php', self.root + 'sites/default/settings.php')
        lines = open(self.root + 'sites/default/settings.php', 'r').readlines()
        task = 'install'
        for text in lines:
            if text == "include 'pcf.php';\n":
                task = 'ignore'
                break
        if task == 'install':
            self.replace_line(self.root + 'sites/default/settings.php', len(lines)-1, lines[-1] + "\ninclude 'pcf.php';\n")
        if self.mysqlcups:
            self.replace_line(self.root + 'sites/default/pcf.php', 7, '      if($ups["name"] == "' + self.mysqlcups + '") {\n')
        if self.memcache:
            self.replace_line(self.root + 'sites/default/pcf.php', 9, '      if($ups["name"] == "' + self.memcache + '") {\n')
        if self.s3fs:
            self.replace_line(self.root + 'sites/default/pcf.php',11, '      if($ups["name"] == "' + self.s3fs + '") {\n')
        if self.varnish:
            self.replace_line(self.root + 'sites/default/pcf.php',13, '      if($ups["name"] == "' + self.varnish + '") {\n')
        if os.path.isdir(self.root + self.modules + 'memcache'):
            self.replace_line(self.root + 'sites/default/pcf.php', 59, "    $conf['cache_backends'][] = 'sites/all/modules/memcache/memcache.inc';\n")
            self.replace_line(self.root + 'sites/default/pcf.php', 60, "    $conf['lock_inc'] = 'sites/all/modules/memcache/memcache-lock.inc';\n")
        if os.path.isdir(self.root + self.modules + 'varnish'):
            self.replace_line(self.root + 'sites/default/pcf.php', 77, "    $conf['cache_backends'][] = 'sites/all/modules/varnish/varnish.cache.inc';\n")
        if os.path.isdir(self.root + self.modules + 'redis'):
            self.replace_line(self.root + 'sites/default/pcf.php', 94, "    $conf['lock_inc'] = 'sites/all/modules/redis/redis.lock.inc';\n")
            self.replace_line(self.root + 'sites/default/pcf.php', 95, "    $conf['path_inc'] = 'sites/all/modules/redis/redis.path.inc';\n")
            self.replace_line(self.root + 'sites/default/pcf.php', 96, "    $conf['cache_backends'][] = 'sites/all/modules/redis/redis.autoload.inc';\n")
    def services(self):
        services = ''
        if self.mysql:
            services += '      - ' + self.mysql + '\n'
        if self.mysqlcups:
            services += '      - ' + self.mysqlcups + '\n'
        if self.s3fs:
            services += '      - ' + self.s3fs + '\n'
        if self.redis:
            services += '      - ' + self.redis + '\n'
        if self.sso:
            services += '      - ' + self.sso + '\n'
        return services
    def copy(self):
        if os.path.isdir(self.root) and os.path.exists(self.root + 'install.php'):
            if os.path.isdir(self.root + '.bp-config') == False:
                copytree('.bp-config', self.root + '.bp-config')
                print '.bp-config copied'
            if os.path.isdir(self.root + self.modules + 'libraries') == False and os.path.isdir(self.root + self.modules + 'contrib/libraries') == False:
                copytree('modules/libraries', self.root + self.modules + 'contrib/libraries')
                if os.path.isdir(self.root + 'sites/all/libraries/awssdk2') == False:
                    copytree('awssdk2', self.root + 'sites/all/libraries/awssdk2')
                    print 'awssdk2 library copied'
            if os.path.isdir(self.root + self.modules + 'oauth2_authentication') == False and os.path.isdir(self.root + self.modules + 'contrib/oauth2_authentication') == False:
                copytree('modules/oauth2_authentication', self.root + self.modules + 'contrib/oauth2_authentication')
                print 'oauth2_authentication copied'
            if os.path.isdir(self.root + self.modules + 'oauth2_client') == False and os.path.isdir(self.root + self.modules + 'contrib/oauth2_client') == False:
                copytree('modules/oauth2_client', self.root + self.modules + 'contrib/oauth2_client')
                print 'oauth2_client copied'
            if os.path.isdir(self.root + self.modules + 'redis') == False and os.path.isdir(self.root + self.modules + 'contrib/redis') == False:
                copytree('modules/redis', self.root + self.modules + 'contrib/redis')
                print 'redis copied'
            if os.path.isdir(self.root + self.modules + 's3fs') == False and os.path.isdir(self.root + self.modules + 'contrib/s3fs') == False:
                copytree('modules/s3fs', self.root + self.modules + 'contrib/s3fs')
                print 's3fs copied'
            if os.path.isdir(self.root + self.modules + 'varnish') == False and os.path.isdir(self.root + self.modules + 'contrib/varnish') == False:
                copytree('modules/varnish', self.root + self.modules + 'contrib/varnish')
                print 'varnish copied'
        else:
            print 'Not a drupal folder'
            sys.exit()
d7pcf()
