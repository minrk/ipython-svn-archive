from lxml import etree as ET

import normal

# These should all compare equal after normalization/c14n
notext_batch = [
('<notebook><head><meta/></head><ipython-log id="default-log"><cell number="1"><input></input>'
 '</cell></ipython-log></notebook>'),

"""<notebook>
    <head>
        <meta/>
    </head>
    <ipython-log id="default-log">
        <cell number="1">
            <input></input>
        </cell>
    </ipython-log>
</notebook>""",
"""<notebook>
    <head>
        <meta/>
    </head>
    <ipython-log id="default-log">
        <cell number="1">
            <input/>
        </cell>
    </ipython-log>
</notebook>""",
]

# These, when written, should compare unequal to those in notext_batch
anti_notext_batch = [
]

stripnewline_batch = [
"""<notebook>
<ipython-log id="default-log">
<cell number="1">
<input>x = 1</input>
</cell>
<cell number="2">
<input>print x</input>
<stdout>1
</stdout>
</cell>
<cell number="3">
<input>x</input>
<output>1</output>
</cell>
</ipython-log>
</notebook>
""",
"""<notebook>
<ipython-log id="default-log">
<cell number="1">
<input>
x = 1
</input>
</cell>
<cell number="2">
<input>
print x
</input>
<stdout>1
</stdout>
</cell>
<cell number="3">
<input>
x
</input>
<output>
1
</output>
</cell>
</ipython-log>
</notebook>
""",
]

anti_stripnewline_batch = []

mixed_batch = [
"""<notebook>
<sheet>
<para>This has <emphasis>mixed</emphasis> content.</para>
</sheet>
</notebook>
""",
"""<notebook>
    <sheet>
        <para>This has <emphasis>mixed</emphasis> content.</para>
    </sheet>
</notebook>
""",
]

anti_mixed_batch = [
"""<notebook>
    <sheet>
        <para>This also has <emphasis>mixed</emphasis>, but different
        content.</para>
    </sheet>
</notebook>
""",
"""<notebook>
    <sheet>
        <para>This has <emphasis>different</emphasis> content.</para>
    </sheet>
</notebook>
""",
"""<notebook>
    <sheet>
        <para>Thishas<emphasis>mixed</emphasis>content.</para>
    </sheet>
</notebook>
""",
]

def test_notext():
    roots = [ET.fromstring(x) for x in notext_batch]
    str0 = normal.c14n(roots[0])
    for i in range(1, len(roots)):
        assert str0 == normal.c14n(roots[i])

def test_anti_notext():
    roots = [ET.fromstring(x) for x in anti_notext_batch]
    str0 = normal.c14n(ET.fromstring(notext_batch[0]))
    for i in range(len(roots)):
        assert str0 != normal.c14n(roots[i])

def test_stripnewline():
    roots = [ET.fromstring(x) for x in stripnewline_batch]
    str0 = normal.c14n(roots[0])
    for i in range(1, len(roots)):
        assert str0 == normal.c14n(roots[i])

def test_anti_stripnewline():
    roots = [ET.fromstring(x) for x in anti_stripnewline_batch]
    str0 = normal.c14n(ET.fromstring(stripnewline_batch[0]))
    for i in range(len(roots)):
        assert str0 != normal.c14n(roots[i])

def test_mixed():
    roots = [ET.fromstring(x) for x in mixed_batch]
    str0 = normal.c14n(roots[0])
    for i in range(1, len(roots)):
        assert str0 == normal.c14n(roots[i])

def test_anti_mixed():
    roots = [ET.fromstring(x) for x in anti_mixed_batch]
    str0 = normal.c14n(ET.fromstring(mixed_batch[0]))
    for i in range(len(roots)):
        assert str0 != normal.c14n(roots[i])
