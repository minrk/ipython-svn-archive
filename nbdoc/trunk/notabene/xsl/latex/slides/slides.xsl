<!--############################################################################# 
|	$Id: slides.xsl,v 1.2 2003/04/07 08:40:23 rcasellas Exp $		
|- #############################################################################
|	$Author: rcasellas $												
|														
|   PURPOSE: 
| 	This is the "parent" stylesheet. The used "modules" are included here.
|	output encoding text in ISO-8859-1 indented.
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

    <xsl:include href="../docbook.xsl"/><xsl:output method="text" encoding="ISO-8859-1" indent="yes"/><xsl:include href="slidesinfo.mod.xsl"/><xsl:include href="slidestoc.mod.xsl"/><xsl:include href="foil.mod.xsl"/><xsl:template match="/">
	<xsl:variable name="xsl-vendor" select="system-property('xsl:vendor')"/>
	<xsl:message>################################################################################</xsl:message>
	<xsl:message> XSLT stylesheets DocBook - LaTeX 2e                                            </xsl:message>
	<xsl:message> SLIDES DTD                                                                     </xsl:message>
	<xsl:message> Reqs: LaTeX 2e installation common packages                                    </xsl:message>
	<xsl:message>################################################################################</xsl:message>
	<xsl:message> RELEASE : <xsl:value-of select="$VERSION"/>                                    </xsl:message>
	<xsl:message> VERSION : <xsl:value-of select="$CVSVERSION"/>                                 </xsl:message>
	<xsl:message>     TAG : <xsl:value-of select="$TAG"/>                                        </xsl:message>
	<xsl:message>     WWW : http://db2latex.sourceforge.net                                      </xsl:message>
	<xsl:message> SUMMARY : http://www.sourceforge.net/projects/db2latex                         </xsl:message>
	<xsl:message>  AUTHOR : Ramon Casellas   casellas@infres.enst.fr                             </xsl:message>
	<xsl:message>  AUTHOR : James Devenish   j-devenish@users.sf.net                             </xsl:message>
	<xsl:message>   USING : <xsl:call-template name="set-vendor"/>                               </xsl:message>
	<xsl:message><xsl:value-of select="$xsl-vendor"/>                                            </xsl:message>
	<xsl:message>################################################################################</xsl:message>
	<xsl:apply-templates/>
    </xsl:template><xsl:param name="db2latex.slides.class" select="'prosper'"/><xsl:param name="db2latex.slides.customclass" select="'rcas'"/><xsl:param name="db2latex.slides.options" select="'pdf,frames,slideColor'"/><xsl:variable name="db2latex.slides.packages">
	<xsl:text>\usepackage[latin1]{inputenc}
</xsl:text>
	<xsl:text>\usepackage{pstricks,pst-node,pst-text,pst-3d}
</xsl:text>
	</xsl:variable><xsl:variable name="db2latex.slides.optpackages">
	<xsl:text>\usepackage{subfigure}
</xsl:text>
	<xsl:text>\usepackage{a4wide}
</xsl:text>
	<xsl:text>\usepackage{times}
</xsl:text>
	<xsl:text>\usepackage{fancyvrb}
</xsl:text>
	<xsl:text>\usepackage{amsmath,amsthm, amsfonts, amssymb, amsxtra,amsopn}
</xsl:text>
	</xsl:variable><xsl:variable name="db2latex.slides.beforebegin">
	<xsl:text>% Definition of new colors
</xsl:text>
	<xsl:text>\newrgbcolor{LemonChiffon}{1. 0.98 0.8}
</xsl:text>
	<xsl:text>\newrgbcolor{LightBlue}{0.68 0.85 0.9}
</xsl:text>
	<xsl:text>\hypersetup{pdfpagemode=FullScreen}
</xsl:text>
	<xsl:text>\makeatletter
</xsl:text>
	<xsl:text>%\newdimen\pst@dimz
</xsl:text>
	</xsl:variable><xsl:template match="slides">
<!-- Document class and preamble -->
	<xsl:text>\documentclass[</xsl:text><xsl:value-of select="$db2latex.slides.options"/>
	<xsl:text>, </xsl:text><xsl:value-of select="$db2latex.slides.customclass"/>
	<xsl:text>]{</xsl:text><xsl:value-of select="$db2latex.slides.class"/>
	<xsl:text>}
</xsl:text>
	<xsl:value-of select="$db2latex.slides.packages"/>
	<xsl:value-of select="$db2latex.slides.optpackages"/>
	<xsl:value-of select="$db2latex.slides.beforebegin"/>
<!-- Process SlidesInfo -->
	<xsl:apply-templates select="slidesinfo"/>
	<xsl:text>\begin{document}
</xsl:text>
	<xsl:text>\maketitle
</xsl:text>
<!-- Process Everything except SlidesInfo -->
	<xsl:apply-templates select="*[not(slidesinfo)]"/>
<!-- <xsl:apply-templates select="foil|foilgroup"/> -->
	<xsl:text>\end{document}
</xsl:text>
    </xsl:template></xsl:stylesheet>