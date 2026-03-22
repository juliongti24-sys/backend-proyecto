import xml.etree.ElementTree as ET

tree = ET.parse('report2.xml')
root = tree.getroot()

with open('failures.txt', 'w', encoding='utf-8') as f:
    for ts in root.findall('testsuite'):
        for tc in ts.findall('testcase'):
            failure = tc.find('failure')
            if failure is not None:
                msg = failure.get('message').split("\n")
                f.write(f"FAIL: {tc.get('name')} | {msg[0]}\n")
