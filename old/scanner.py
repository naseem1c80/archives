import pyinsane2

def scan_documentg(output_path):
    pyinsane2.init()
    devices = pyinsane2.get_devices()
    if not devices:
        raise Exception("لم يتم العثور على ماسح ضوئي.")
    scanner = devices[0]

    scan_session = scanner.scan(multiple=False)
    while not scan_session.done:
        scan_session.scan.read()
    
    image = scan_session.images[0]
    image.save(output_path)

    pyinsane2.exit()
    return output_path

def scan_document(output_path="static/scanned.png"):
    pyinsane2.init()
    devices = pyinsane2.get_devices()
    if not devices:
        return output_path
        #raise Exception("لم يتم العثور على ماسح.")
    scanner = devices[0]
    session = scanner.scan(multiple=False)

    while not session.done:
        session.scan.read()

    image = session.images[0]
    image.save(output_path)
    pyinsane2.exit()
    return output_path

