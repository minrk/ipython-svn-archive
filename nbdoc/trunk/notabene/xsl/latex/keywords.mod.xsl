<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: keywords.mod.xsl,v 1.7 2004/01/09 12:02:15 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="keywordset">
		<xsl:call-template name="map.begin"/>
		<xsl:call-template name="gentext.template">
			<xsl:with-param name="context" select="'naturalblocklist'"/>
			<xsl:with-param name="name" select="'start'"/>
		</xsl:call-template>
		<xsl:apply-templates/>
		<xsl:call-template name="gentext.template">
			<xsl:with-param name="context" select="'naturalblocklist'"/>
			<xsl:with-param name="name" select="'end'"/>
		</xsl:call-template>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="keyword">
		<xsl:if test="position() &gt; 1">
			<xsl:choose>
				<xsl:when test="position()=last() and position() &gt; 2">
					<xsl:call-template name="gentext.template">
						<xsl:with-param name="context" select="'naturalblocklist'"/>
						<xsl:with-param name="name" select="'lastofmany'"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:when test="position()=last()">
					<xsl:call-template name="gentext.template">
						<xsl:with-param name="context" select="'naturalblocklist'"/>
						<xsl:with-param name="name" select="'lastoftwo'"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="gentext.template">
						<xsl:with-param name="context" select="'naturalblocklist'"/>
						<xsl:with-param name="name" select="'middle'"/>
					</xsl:call-template>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:if>
		<xsl:call-template name="inline.charseq"/>
	</xsl:template><xsl:template match="subjectset"/></xsl:stylesheet>
