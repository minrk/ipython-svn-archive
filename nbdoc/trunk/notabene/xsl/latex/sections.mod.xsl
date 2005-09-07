<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: sections.mod.xsl,v 1.8 2004/01/03 12:19:15 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="sect1|sect2|sect3|sect4|sect5">
		<xsl:param name="bridgehead" select="ancestor::preface|ancestor::colophon|ancestor::dedication|ancestor::partintro"/>
		<xsl:variable name="template">
			<xsl:value-of select="local-name(.)"/>
			<xsl:if test="$bridgehead"><xsl:text>*</xsl:text></xsl:if>
		</xsl:variable>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="keyword" select="$template"/>
		</xsl:call-template>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end">
			<xsl:with-param name="keyword" select="$template"/>
		</xsl:call-template>
	</xsl:template><xsl:template match="section|simplesect">
		<xsl:param name="bridgehead" select="ancestor::preface|ancestor::colophon|ancestor::dedication"/>
		<xsl:param name="level" select="count(ancestor::section)+1"/>
		<xsl:variable name="template">
			<xsl:choose>
				<xsl:when test="$level&lt;6">
					<xsl:text>sect</xsl:text>
					<xsl:value-of select="$level"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:message>DB2LaTeX: recursive section|simplesect &gt; 5 not well supported.</xsl:message>
					<xsl:text>sect6</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:if test="$bridgehead"><xsl:text>*</xsl:text></xsl:if>
		</xsl:variable>
		<xsl:text>
</xsl:text>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="keyword" select="$template"/>
		</xsl:call-template>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end">
			<xsl:with-param name="keyword" select="$template"/>
		</xsl:call-template>
	</xsl:template></xsl:stylesheet>
