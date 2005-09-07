<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: abstract.mod.xsl,v 1.12 2003/12/30 13:38:04 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="abstract">
		<xsl:variable name="keyword">
			<xsl:value-of select="local-name(.)"/>
			<xsl:if test="title">
				<!-- choose a different mapping -->
				<xsl:text>-title</xsl:text>
			</xsl:if>
		</xsl:variable>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="keyword" select="$keyword"/>
		</xsl:call-template>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end">
			<xsl:with-param name="keyword" select="$keyword"/>
		</xsl:call-template>
	</xsl:template></xsl:stylesheet>
