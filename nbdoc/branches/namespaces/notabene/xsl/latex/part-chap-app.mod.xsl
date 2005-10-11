<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: part-chap-app.mod.xsl,v 1.7 2004/01/18 11:56:29 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="set|part|chapter">
		<xsl:call-template name="map.begin"/>
		<xsl:call-template name="content-templates-rootid"/>
		<xsl:call-template name="map.end"/>
	</xsl:template><!--
    <doc:template match="chapter" xmlns="">
	<refpurpose> XSL template for Chapters.</refpurpose>
	<doc:description>
	    <para> This is the main entry point for a <sgmltag class="start">chapter</sgmltag> subtree.
		This template processes any chapter. Outputs <literal>\chapter{title}</literal>, calls 
		templates and apply-templates. Since chapters only apply in books, 
		some assumptions could be done in order to optimize the stylesheet behaviour.</para>

	    <formalpara><title>Remarks and Bugs</title>
		<itemizedlist>
		    <listitem><para> 
			EMPTY templates: chapter/title, 
			chapter/titleabbrev, 
			chapter/subtitle, 
			chapter/docinfo|chapterinfo.</para></listitem>
		</itemizedlist>
	    </formalpara>

	    <formalpara><title>Affected by</title> map. 
	    </formalpara>
	</doc:description>
    </doc:template>
	--><xsl:template match="appendix">
		<xsl:if test="not (preceding-sibling::appendix)">
			<xsl:text>
</xsl:text>
			<xsl:choose>
				<xsl:when test="local-name(..)='book' or local-name(..)='part'">
					<xsl:text>\newcommand{\dbappendix}[1]{\chapter{#1}}%
</xsl:text>
					<xsl:call-template name="map.begin">
						<xsl:with-param name="keyword">appendices-chapter</xsl:with-param>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>\newcommand{\dbappendix}[1]{\section{#1}}%
</xsl:text>
					<xsl:call-template name="map.begin">
						<xsl:with-param name="keyword">appendices-section</xsl:with-param>
					</xsl:call-template>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:if>
		<xsl:call-template name="map.begin"/>
		<xsl:call-template name="content-templates"/>
		<xsl:call-template name="map.end"/>
		<xsl:if test="not (following-sibling::appendix)">
			<xsl:text>
</xsl:text>
			<xsl:choose>
				<xsl:when test="local-name(..)='book' or local-name(..)='part'">
					<xsl:call-template name="map.end">
						<xsl:with-param name="keyword">appendices-chapter</xsl:with-param>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="map.end">
						<xsl:with-param name="keyword">appendices-section</xsl:with-param>
					</xsl:call-template>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:text>
</xsl:text>
		</xsl:if>
	</xsl:template></xsl:stylesheet>
