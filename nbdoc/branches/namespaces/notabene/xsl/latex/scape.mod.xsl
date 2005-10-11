<?xml version="1.0"?>
<!-- This file was generated automatically. -->
<!-- Developers should not commit sundry patches against this file. -->
<!-- The source file (with documentation!) is in the admin directory. -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template name="scape">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">&lt;</xsl:with-param>
      <xsl:with-param name="to">\textless{}</xsl:with-param>
      <xsl:with-param name="string">
        <xsl:call-template name="string-replace">
          <xsl:with-param name="from">&gt;</xsl:with-param>
          <xsl:with-param name="to">\textgreater{}</xsl:with-param>
          <xsl:with-param name="string">
            <xsl:call-template name="string-replace">
              <xsl:with-param name="from">~</xsl:with-param>
              <xsl:with-param name="to">\textasciitilde{}</xsl:with-param>
              <xsl:with-param name="string">
                <xsl:call-template name="string-replace">
                  <xsl:with-param name="from">^</xsl:with-param>
                  <xsl:with-param name="to">\textasciicircum{}</xsl:with-param>
                  <xsl:with-param name="string">
                    <xsl:call-template name="string-replace">
                      <xsl:with-param name="from">&amp;</xsl:with-param>
                      <xsl:with-param name="to">\&amp;</xsl:with-param>
                      <xsl:with-param name="string">
                        <xsl:call-template name="string-replace">
                          <xsl:with-param name="from">#</xsl:with-param>
                          <xsl:with-param name="to">\#</xsl:with-param>
                          <xsl:with-param name="string">
                            <xsl:call-template name="string-replace">
                              <xsl:with-param name="from">_</xsl:with-param>
                              <xsl:with-param name="to">\_</xsl:with-param>
                              <xsl:with-param name="string">
                                <xsl:call-template name="string-replace">
                                  <xsl:with-param name="from">$</xsl:with-param>
                                  <xsl:with-param name="to">\$</xsl:with-param>
                                  <xsl:with-param name="string">
                                    <xsl:call-template name="string-replace">
                                      <xsl:with-param name="from">%</xsl:with-param>
                                      <xsl:with-param name="to">\%</xsl:with-param>
                                      <xsl:with-param name="string">
                                        <xsl:call-template name="string-replace">
                                          <xsl:with-param name="from">|</xsl:with-param>
                                          <xsl:with-param name="to">\docbooktolatexpipe{}</xsl:with-param>
                                          <xsl:with-param name="string">
                                            <xsl:call-template name="string-replace">
                                              <xsl:with-param name="from">{</xsl:with-param>
                                              <xsl:with-param name="to">\{</xsl:with-param>
                                              <xsl:with-param name="string">
                                                <xsl:call-template name="string-replace">
                                                  <xsl:with-param name="from">}</xsl:with-param>
                                                  <xsl:with-param name="to">\}</xsl:with-param>
                                                  <xsl:with-param name="string">
                                                    <xsl:call-template name="string-replace">
                                                      <xsl:with-param name="from">\textbackslash  </xsl:with-param>
                                                      <xsl:with-param name="to">\textbackslash \ </xsl:with-param>
                                                      <xsl:with-param name="string">
                                                        <xsl:call-template name="string-replace">
                                                          <xsl:with-param name="from">\</xsl:with-param>
                                                          <xsl:with-param name="to">\textbackslash </xsl:with-param>
                                                          <xsl:with-param name="string" select="$string"/>
                                                        </xsl:call-template>
                                                      </xsl:with-param>
                                                    </xsl:call-template>
                                                  </xsl:with-param>
                                                </xsl:call-template>
                                              </xsl:with-param>
                                            </xsl:call-template>
                                          </xsl:with-param>
                                        </xsl:call-template>
                                      </xsl:with-param>
                                    </xsl:call-template>
                                  </xsl:with-param>
                                </xsl:call-template>
                              </xsl:with-param>
                            </xsl:call-template>
                          </xsl:with-param>
                        </xsl:call-template>
                      </xsl:with-param>
                    </xsl:call-template>
                  </xsl:with-param>
                </xsl:call-template>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template><xsl:template name="scape-indexterm">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">!</xsl:with-param>
      <xsl:with-param name="to">"!</xsl:with-param>
      <xsl:with-param name="string">
        <xsl:call-template name="string-replace">
          <xsl:with-param name="from">|</xsl:with-param>
          <xsl:with-param name="to">\ensuremath{"|}</xsl:with-param>
          <xsl:with-param name="string">
            <xsl:call-template name="string-replace">
              <xsl:with-param name="from">@</xsl:with-param>
              <xsl:with-param name="to">"@</xsl:with-param>
              <xsl:with-param name="string">
                <xsl:call-template name="string-replace">
                  <xsl:with-param name="from">&lt;</xsl:with-param>
                  <xsl:with-param name="to">\textless{}</xsl:with-param>
                  <xsl:with-param name="string">
                    <xsl:call-template name="string-replace">
                      <xsl:with-param name="from">&gt;</xsl:with-param>
                      <xsl:with-param name="to">\textgreater{}</xsl:with-param>
                      <xsl:with-param name="string">
                        <xsl:call-template name="string-replace">
                          <xsl:with-param name="from">~</xsl:with-param>
                          <xsl:with-param name="to">\textasciitilde{}</xsl:with-param>
                          <xsl:with-param name="string">
                            <xsl:call-template name="string-replace">
                              <xsl:with-param name="from">^</xsl:with-param>
                              <xsl:with-param name="to">\textasciicircum{}</xsl:with-param>
                              <xsl:with-param name="string">
                                <xsl:call-template name="string-replace">
                                  <xsl:with-param name="from">&amp;</xsl:with-param>
                                  <xsl:with-param name="to">\&amp;</xsl:with-param>
                                  <xsl:with-param name="string">
                                    <xsl:call-template name="string-replace">
                                      <xsl:with-param name="from">#</xsl:with-param>
                                      <xsl:with-param name="to">\#</xsl:with-param>
                                      <xsl:with-param name="string">
                                        <xsl:call-template name="string-replace">
                                          <xsl:with-param name="from">_</xsl:with-param>
                                          <xsl:with-param name="to">\_</xsl:with-param>
                                          <xsl:with-param name="string">
                                            <xsl:call-template name="string-replace">
                                              <xsl:with-param name="from">$</xsl:with-param>
                                              <xsl:with-param name="to">\$</xsl:with-param>
                                              <xsl:with-param name="string">
                                                <xsl:call-template name="string-replace">
                                                  <xsl:with-param name="from">%</xsl:with-param>
                                                  <xsl:with-param name="to">\%</xsl:with-param>
                                                  <xsl:with-param name="string">
                                                    <xsl:call-template name="string-replace">
                                                      <xsl:with-param name="from">\}</xsl:with-param>
                                                      <xsl:with-param name="to">\textbraceright{}</xsl:with-param>
                                                      <xsl:with-param name="string">
                                                        <xsl:call-template name="string-replace">
                                                          <xsl:with-param name="from">{</xsl:with-param>
                                                          <xsl:with-param name="to">\textbraceleft{}</xsl:with-param>
                                                          <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">}</xsl:with-param>
                                                            <xsl:with-param name="to">\}</xsl:with-param>
                                                            <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">"</xsl:with-param>
                                                            <xsl:with-param name="to">""</xsl:with-param>
                                                            <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">\textbackslash  </xsl:with-param>
                                                            <xsl:with-param name="to">\textbackslash \ </xsl:with-param>
                                                            <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">\</xsl:with-param>
                                                            <xsl:with-param name="to">\textbackslash </xsl:with-param>
                                                            <xsl:with-param name="string" select="$string"/>
                                                            </xsl:call-template>
                                                            </xsl:with-param>
                                                            </xsl:call-template>
                                                            </xsl:with-param>
                                                            </xsl:call-template>
                                                            </xsl:with-param>
                                                            </xsl:call-template>
                                                          </xsl:with-param>
                                                        </xsl:call-template>
                                                      </xsl:with-param>
                                                    </xsl:call-template>
                                                  </xsl:with-param>
                                                </xsl:call-template>
                                              </xsl:with-param>
                                            </xsl:call-template>
                                          </xsl:with-param>
                                        </xsl:call-template>
                                      </xsl:with-param>
                                    </xsl:call-template>
                                  </xsl:with-param>
                                </xsl:call-template>
                              </xsl:with-param>
                            </xsl:call-template>
                          </xsl:with-param>
                        </xsl:call-template>
                      </xsl:with-param>
                    </xsl:call-template>
                  </xsl:with-param>
                </xsl:call-template>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template><xsl:template name="scape-verbatim">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">~</xsl:with-param>
      <xsl:with-param name="to">\textasciitilde{}</xsl:with-param>
      <xsl:with-param name="string">
        <xsl:call-template name="string-replace">
          <xsl:with-param name="from">^</xsl:with-param>
          <xsl:with-param name="to">\textasciicircum{}</xsl:with-param>
          <xsl:with-param name="string">
            <xsl:call-template name="string-replace">
              <xsl:with-param name="from">&amp;</xsl:with-param>
              <xsl:with-param name="to">\&amp;</xsl:with-param>
              <xsl:with-param name="string">
                <xsl:call-template name="string-replace">
                  <xsl:with-param name="from">#</xsl:with-param>
                  <xsl:with-param name="to">\#</xsl:with-param>
                  <xsl:with-param name="string">
                    <xsl:call-template name="string-replace">
                      <xsl:with-param name="from">_</xsl:with-param>
                      <xsl:with-param name="to">\_\dbz{}</xsl:with-param>
                      <xsl:with-param name="string">
                        <xsl:call-template name="string-replace">
                          <xsl:with-param name="from">$</xsl:with-param>
                          <xsl:with-param name="to">\$</xsl:with-param>
                          <xsl:with-param name="string">
                            <xsl:call-template name="string-replace">
                              <xsl:with-param name="from">%</xsl:with-param>
                              <xsl:with-param name="to">\%</xsl:with-param>
                              <xsl:with-param name="string">
                                <xsl:call-template name="string-replace">
                                  <xsl:with-param name="from">/</xsl:with-param>
                                  <xsl:with-param name="to">/\dbz{}</xsl:with-param>
                                  <xsl:with-param name="string">
                                    <xsl:call-template name="string-replace">
                                      <xsl:with-param name="from">-</xsl:with-param>
                                      <xsl:with-param name="to">-\dbz{}</xsl:with-param>
                                      <xsl:with-param name="string">
                                        <xsl:call-template name="string-replace">
                                          <xsl:with-param name="from">+</xsl:with-param>
                                          <xsl:with-param name="to">+\dbz{}</xsl:with-param>
                                          <xsl:with-param name="string">
                                            <xsl:call-template name="string-replace">
                                              <xsl:with-param name="from">.</xsl:with-param>
                                              <xsl:with-param name="to">.\dbz{}</xsl:with-param>
                                              <xsl:with-param name="string">
                                                <xsl:call-template name="string-replace">
                                                  <xsl:with-param name="from">(</xsl:with-param>
                                                  <xsl:with-param name="to">(\dbz{}</xsl:with-param>
                                                  <xsl:with-param name="string">
                                                    <xsl:call-template name="string-replace">
                                                      <xsl:with-param name="from">)</xsl:with-param>
                                                      <xsl:with-param name="to">)\dbz{}</xsl:with-param>
                                                      <xsl:with-param name="string">
                                                        <xsl:call-template name="string-replace">
                                                          <xsl:with-param name="from">"</xsl:with-param>
                                                          <xsl:with-param name="to">"{}</xsl:with-param>
                                                          <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">{</xsl:with-param>
                                                            <xsl:with-param name="to">\docbooktolatexgobble\string\{</xsl:with-param>
                                                            <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">}</xsl:with-param>
                                                            <xsl:with-param name="to">\docbooktolatexgobble\string\}</xsl:with-param>
                                                            <xsl:with-param name="string">
                                                            <xsl:call-template name="string-replace">
                                                            <xsl:with-param name="from">\</xsl:with-param>
                                                            <xsl:with-param name="to">\docbooktolatexgobble\string\\</xsl:with-param>
                                                            <xsl:with-param name="string" select="$string"/>
                                                            </xsl:call-template>
                                                            </xsl:with-param>
                                                            </xsl:call-template>
                                                            </xsl:with-param>
                                                            </xsl:call-template>
                                                          </xsl:with-param>
                                                        </xsl:call-template>
                                                      </xsl:with-param>
                                                    </xsl:call-template>
                                                  </xsl:with-param>
                                                </xsl:call-template>
                                              </xsl:with-param>
                                            </xsl:call-template>
                                          </xsl:with-param>
                                        </xsl:call-template>
                                      </xsl:with-param>
                                    </xsl:call-template>
                                  </xsl:with-param>
                                </xsl:call-template>
                              </xsl:with-param>
                            </xsl:call-template>
                          </xsl:with-param>
                        </xsl:call-template>
                      </xsl:with-param>
                    </xsl:call-template>
                  </xsl:with-param>
                </xsl:call-template>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template><xsl:template name="scape-href">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">&amp;</xsl:with-param>
      <xsl:with-param name="to">\&amp;</xsl:with-param>
      <xsl:with-param name="string">
        <xsl:call-template name="string-replace">
          <xsl:with-param name="from">%</xsl:with-param>
          <xsl:with-param name="to">\%</xsl:with-param>
          <xsl:with-param name="string">
            <xsl:call-template name="string-replace">
              <xsl:with-param name="from">[</xsl:with-param>
              <xsl:with-param name="to">\[</xsl:with-param>
              <xsl:with-param name="string">
                <xsl:call-template name="string-replace">
                  <xsl:with-param name="from">]</xsl:with-param>
                  <xsl:with-param name="to">\]</xsl:with-param>
                  <xsl:with-param name="string">
                    <xsl:call-template name="string-replace">
                      <xsl:with-param name="from">{</xsl:with-param>
                      <xsl:with-param name="to">\{</xsl:with-param>
                      <xsl:with-param name="string">
                        <xsl:call-template name="string-replace">
                          <xsl:with-param name="from">}</xsl:with-param>
                          <xsl:with-param name="to">\}</xsl:with-param>
                          <xsl:with-param name="string">
                            <xsl:call-template name="string-replace">
                              <xsl:with-param name="from">\</xsl:with-param>
                              <xsl:with-param name="to">\docbooktolatexgobble\string\\</xsl:with-param>
                              <xsl:with-param name="string" select="$string"/>
                            </xsl:call-template>
                          </xsl:with-param>
                        </xsl:call-template>
                      </xsl:with-param>
                    </xsl:call-template>
                  </xsl:with-param>
                </xsl:call-template>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template><xsl:template name="scape-url">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">&amp;</xsl:with-param>
      <xsl:with-param name="to">\string&amp;</xsl:with-param>
      <xsl:with-param name="string">
        <xsl:call-template name="string-replace">
          <xsl:with-param name="from">%</xsl:with-param>
          <xsl:with-param name="to">\%</xsl:with-param>
          <xsl:with-param name="string">
            <xsl:call-template name="string-replace">
              <xsl:with-param name="from">{</xsl:with-param>
              <xsl:with-param name="to">\{</xsl:with-param>
              <xsl:with-param name="string">
                <xsl:call-template name="string-replace">
                  <xsl:with-param name="from">}</xsl:with-param>
                  <xsl:with-param name="to">\}</xsl:with-param>
                  <xsl:with-param name="string">
                    <xsl:call-template name="string-replace">
                      <xsl:with-param name="from">\</xsl:with-param>
                      <xsl:with-param name="to">\docbooktolatexgobble\string\\</xsl:with-param>
                      <xsl:with-param name="string" select="$string"/>
                    </xsl:call-template>
                  </xsl:with-param>
                </xsl:call-template>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template><xsl:template name="scape-optionalarg">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">]</xsl:with-param>
      <xsl:with-param name="to">{\rbrack}</xsl:with-param>
      <xsl:with-param name="string" select="$string"/>
    </xsl:call-template>
  </xsl:template><xsl:template name="scape-slash">
    <xsl:param name="string"/>
    <xsl:call-template name="string-replace">
      <xsl:with-param name="from">.</xsl:with-param>
      <xsl:with-param name="to">.\dbz{}</xsl:with-param>
      <xsl:with-param name="string">
        <xsl:call-template name="string-replace">
          <xsl:with-param name="from">/</xsl:with-param>
          <xsl:with-param name="to">/\dbz{}</xsl:with-param>
          <xsl:with-param name="string" select="$string"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template></xsl:stylesheet>
