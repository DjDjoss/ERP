import shutil, datetime, os
base = os.path.abspath(os.path.join(os.getcwd(), '..'))
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
dest = os.path.join(base, f'ERP_Rosan_backup_{ts}')
shutil.make_archive(dest, 'zip', os.getcwd())
print('Backup created:', dest + '.zip')
