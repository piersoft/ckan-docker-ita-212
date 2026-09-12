"""pyoai (2013) importa pkg_resources solo per leggere la propria versione nel
tag <toolkit> di Identify; i setuptools recenti non lo forniscono piu'.
Eseguito a build time dal Dockerfile dopo l'installazione di ckanext-oai-pmh-server."""
import os
import re

import oaipmh

p = os.path.join(os.path.dirname(oaipmh.__file__), 'common.py')
s = open(p).read()
s = s.replace("import pkg_resources\n", "")
s = re.sub(r"req = pkg_resources\.Requirement\.parse\('pyoai'\)\n\s*egg = pkg_resources\.working_set\.find\(req\)",
           "egg = None  # ckan-docker-ita: patch, vedi patch_pyoai.py", s)
open(p, 'w').write(s)
assert 'pkg_resources' not in s, 'patch pyoai fallita'
print('pyoai patched OK:', p)
