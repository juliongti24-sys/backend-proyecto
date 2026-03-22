import xml.etree.ElementTree as ET

tree = ET.parse('report.xml')
root = tree.getroot()
with open('errors.txt', 'w', encoding='utf-8') as f:
    for ts in root.findall('testsuite'):
        for tc in ts.findall('testcase'):
             failure = tc.find('failure')
             error = tc.find('error')
             if failure is not None:
                  f.write(f"FAILED: {tc.get('name')} - {failure.get('message')}\n")
             elif error is not None:
                  f.write(f"ERROR: {tc.get('name')} - {error.get('message')}\n")
