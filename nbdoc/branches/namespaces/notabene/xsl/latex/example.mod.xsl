<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: example.mod.xsl,v 1.9 2004/01/26 09:40:43 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="example">
		<xsl:variable name="placement">
			<xsl:call-template name="generate.formal.title.placement">
				<xsl:with-param name="object" select="local-name(.)"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="caption">
			<xsl:text>{</xsl:text>
			<xsl:value-of select="$latex.example.caption.style"/>
			<xsl:text>{\caption{</xsl:text>
			<xsl:apply-templates select="title" mode="caption.mode"/>
			<xsl:text>}</xsl:text>
			<xsl:call-template name="label.id"/>
			<xsl:text>}}
</xsl:text>
		</xsl:variable>
		<xsl:call-template name="map.begin"/>
		<xsl:if test="$placement='before'">
			<xsl:text>\captionswapskip{}</xsl:text>
			<xsl:value-of select="$caption"/>
			<xsl:text>\captionswapskip{}</xsl:text>
		</xsl:if>
		<xsl:call-template name="content-templates"/>
		<xsl:if test="$placement!='before'"><xsl:value-of select="$caption"/></xsl:if>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="informalexample">
		<xsl:call-template name="informal.object"/>
	</xsl:template></xsl:stylesheet>
