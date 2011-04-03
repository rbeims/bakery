#!/usr/bin/env python

conf_testmatrix = (

    ("hello = \"world\"\n",
     {'hello':{'val':'world'}}),

    ("foo = 'bar'\n",
     {'foo':{'val':'bar'}}),

    ("foo = 'bar'",
     {'foo':{'val':'bar'}}),

    ("\nfoo = 'bar'",
     {'foo':{'val':'bar'}}),

    ("foo = 'bar'\n\n",
     {'foo':{'val':'bar'}}),

    ("export foo = 'bar'\n",
     {'foo':{'val':'bar','export':True}}),

    ("export foo\n",
     {'foo':{'export':True}}),

    ("foo='bar'\nexport foo\n",
     {'foo':{'val':'bar','export':True}}),

    ("export foo\nfoo='bar'\n",
     {'foo':{'val':'bar','export':True}}),

    ("hello = \"world\"\nfoo = 'bar'\n",
     {'hello':{'val':'world'}, 'foo':{'val':'bar'}}),

    ("hello = \"world\"\nfoo = 'bar'\nint = 42\ntrue = True\nfalse = False\n",
     {'hello':{'val':'world'},
      'foo':{'val':'bar'},
      'int':{'val':42},
      'true':{'val':True},
      'false':{'val':False}}),

    ("multiline = \"foo    \\\nbar \\\nhello world\"\n",
     {'multiline':{'val':'foo    bar hello world'}}),


    (r"""foo = 'bar'
# en kommentar
  # endnu en kommentar
hello = 'world'""",
     {'foo':{'val':'bar'}, 'hello':{'val':'world'}}),

    ("test = 'foo'\ntest += 'bar'\n",
     {'test':{'val':'foo bar'}}),

    ("test = 'foo'\ntest .= 'bar'\n",
     {'test':{'val':'foobar'}}),

    ("test = 'foo'\ntest =+ 'bar'\n",
     {'test':{'val':'bar foo'}}),

    ("test = 'foo'\ntest =. 'bar'\n",
     {'test':{'val':'barfoo'}}),
     
    ("withspace = \"foo bar\"\n",
     {'withspace':{'val':'foo bar'}}),

    ('quoteesc1 = "foo \\\"bar"\n',
     {'quoteesc1':{'val':'foo "bar'}}),

    ("quoteesc1 = 'foo \\\'bar'\n",
     {'quoteesc1':{'val':"foo 'bar"}}),

    ("hest[pony] = 'ko'\n",
     {'hest':{'pony':"ko"}}),

    ("include /tmp/foobar.inc\n",
     {'foo':{'val':'bar'}}),

    ("include /tmp/foobar-no-such-thing.inc\n",
     {}),

    ("require /tmp/foobar.inc\n",
     {'foo':{'val':'bar'}}),

    #("require /home/esben/oe-lite/master/conf/oe-lite.conf\n",
    # {'foo':{'val':'bar'}}),

)

bb_testmatrix = (

    ("do_foobar () {\n  set -ex\n  echo hello world\n}\n",
     {'do_foobar':{'func':'sh','val':'  set -ex\n  echo hello world\n'}}),

    ("fakeroot do_foobar () {\n  set -ex\n  echo hello world\n}\n",
     {'do_foobar':{'func':'sh','fakeroot':True,
                   'val':'  set -ex\n  echo hello world\n'}}),

    ("python do_foobar () {\n  import sys\n  print \"hello world\"\n}\n",
     {'do_foobar':{'func':'python',
                   'val':'  import sys\n  print \"hello world\"\n'}}),
)

expand_testmatrix = (
    ('foo', 'foo'),
    ('${FOO}', 'bar'),
    ('xxx${FOO}', 'xxxbar'),
    ('${FOO}xxx', 'barxxx'),
    ('${FOO}${BAR}', 'barhello world'),
    ('${FOO}xxx${BAR}', 'barxxxhello world'),
    ('xxx${FOO}xxx', 'xxxbarxxx'),
    ('${F${oo}}', 'bar'),
    ('${${foo}}', 'bar'),
    ('${@["foo","bar"][0]}', 'foo'),
    ('${@["${FOO}","foo"][0]}', 'bar'),
    ('$ og {@ $ }', '$ og {@ $ }'),
)

if __name__ == "__main__":
    import confparse, bbparse, expandparse
    f = open("/tmp/foobar.inc", "w")
    f.write("foo='bar'\n")
    f.close()

    parser = confparse.ConfParser()
    passed = failed = 0
    for (testdata,expected_result) in conf_testmatrix:
        print "\n" + repr(testdata)
        parser.lextest(testdata, debug=True)
        result = parser.yacctest(testdata)
        if result.dict != expected_result:
            print "result=%s\nexpected=%s\nFAIL"%(result, expected_result)
            failed += 1
        else:
            print "PASS"
            passed += 1
    print "\nPASSED = %d    FAILED = %d"%(passed, failed)

    parser = bbparse.BBParser()
    passed = failed = 0
    for (testdata,expected_result) in conf_testmatrix + bb_testmatrix:
        print "\n" + repr(testdata)
        parser.lextest(testdata, debug=True)
        result = parser.yacctest(testdata)
        if result.dict != expected_result:
            print "result=%s\nexpected=%s\nFAIL"%(result, expected_result)
            failed += 1
        else:
            print "PASS"
            passed += 1
    print "\nPASSED = %d    FAILED = %d"%(passed, failed)

    data = parser.yacctest("FOO='bar'\nBAR='hello world'\nfoo='FOO'\noo='OO'")

    parser = expandparse.ExpandParser(data)
    passed = failed = 0
    for (testdata,expected_result) in expand_testmatrix:
        print "\n" + repr(testdata)
        parser.lextest(testdata, debug=True)
        result = parser.expand(testdata)
        if result != expected_result:
            print "result=%s\nexpected=%s\nFAIL"%(result, expected_result)
            failed += 1
        else:
            print "PASS"
            passed += 1
    print "\nPASSED = %d    FAILED = %d"%(passed, failed)

