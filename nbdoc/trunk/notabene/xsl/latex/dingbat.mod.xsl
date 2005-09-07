<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: dingbat.mod.xsl,v 1.4 2004/01/02 05:11:38 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template name="dingbat">
		<xsl:param name="dingbat">bullet</xsl:param>
		<xsl:choose>
			<xsl:when test="$dingbat='bullet'"> $\bullet$ </xsl:when>
			<xsl:when test="$dingbat='copyright'">\copyright{}</xsl:when>
			<xsl:when test="$dingbat='trademark'">\texttrademark{}</xsl:when>
			<xsl:when test="$dingbat='registered'">\textregistered{}</xsl:when>
			<xsl:when test="$dingbat='nbsp'">~</xsl:when>
			<xsl:when test="$dingbat='ldquo'">``</xsl:when>
			<xsl:when test="$dingbat='rdquo'">''</xsl:when>
			<xsl:when test="$dingbat='lsquo'">`</xsl:when>
			<xsl:when test="$dingbat='rsquo'">'</xsl:when>
			<xsl:when test="$dingbat='em-dash'">---</xsl:when>
			<xsl:when test="$dingbat='mdash'">---</xsl:when>
			<xsl:when test="$dingbat='en-dash'">--</xsl:when>
			<xsl:when test="$dingbat='ndash'">--</xsl:when>
			<xsl:otherwise>
			<xsl:text> [dingbat?] </xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template></xsl:stylesheet>
