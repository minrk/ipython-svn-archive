<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: graphic.mod.xsl,v 1.5 2004/01/02 07:25:45 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="screenshot">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="screeninfo"/><xsl:template match="graphic">
		<xsl:text>

</xsl:text>
		<xsl:call-template name="inlinegraphic"/>
		<xsl:text>

</xsl:text>
	</xsl:template><xsl:template match="inlinegraphic" name="inlinegraphic">
		<xsl:text>\includegraphics{</xsl:text>
		<xsl:choose>
			<xsl:when test="@entityref">
				<xsl:value-of select="unparsed-entity-uri(@entityref)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="@fileref"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:text>}</xsl:text>
	</xsl:template></xsl:stylesheet>
