<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: para.mod.xsl,v 1.16 2004/01/13 14:17:45 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
|														
|   PURPOSE:
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">


	<!--############################################################################# --><!-- DOCUMENTATION                                                                --><xsl:template name="latex.noparskip">
		<xsl:if test="$latex.use.parskip=1">
			<xsl:text>\docbooktolatexnoparskip
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template name="latex.restoreparskip">
		<xsl:if test="$latex.use.parskip=1">
			<xsl:text>\docbooktolatexrestoreparskip
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="para|simpara">
		<xsl:text>
</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template match="formalpara">
		<xsl:text>
{</xsl:text>
		<xsl:value-of select="$latex.formalpara.title.style"/>
		<xsl:text>{{</xsl:text>
		<xsl:apply-templates select="title"/>
		<xsl:text>}</xsl:text>
		<xsl:call-template name="generate.formalpara.title.delimiter"/>
		<xsl:text>}}\ </xsl:text>
		<xsl:apply-templates select="node()[not(self::title)]"/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template name="generate.formalpara.title.delimiter">
		<xsl:text>.</xsl:text>
	</xsl:template><xsl:template match="textobject/para|step/para|entry/para|question/para" name="para-noline">
		<xsl:if test="position()&gt;1">
			<xsl:text> </xsl:text>
		</xsl:if>
		<xsl:apply-templates/>
		<xsl:if test="position()&lt;last()">
			<xsl:text> </xsl:text>
		</xsl:if>
	</xsl:template></xsl:stylesheet>
