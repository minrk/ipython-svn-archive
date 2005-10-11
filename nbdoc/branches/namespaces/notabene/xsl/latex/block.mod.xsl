<?xml version="1.0"?>
<!--#############################################################################
|	$Id: block.mod.xsl,v 1.16 2004/11/24 02:23:45 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template name="content-templates">
		<xsl:param name="info" select="concat(local-name(.),'info')"/>
		<xsl:apply-templates select="node()[not(self::title or self::subtitle or self::titleabbrev or self::blockinfo or self::docinfo or local-name(.)=$info)]"/>
	</xsl:template><xsl:template name="content-templates-rootid">
		<!--
		<xsl:message>Rootid <xsl:value-of select="$rootid"/></xsl:message>
		<xsl:message>local-name(.) <xsl:value-of select="local-name(.)"/></xsl:message>
		<xsl:message>count(ancestor::*) <xsl:value-of select="count(ancestor::*)"/></xsl:message>
		-->
		<xsl:choose>
			<xsl:when test="$rootid != '' and count(ancestor::*) = 0">
				<xsl:variable name="node" select="key('id', $rootid)"/>
				<xsl:message>count($node) <xsl:value-of select="count($node)"/></xsl:message>
				<xsl:choose>
					<xsl:when test="count($node) = 0">
						<xsl:message terminate="yes">
							<xsl:text>Root ID '</xsl:text>
							<xsl:value-of select="$rootid"/>
							<xsl:text>' not found in document.</xsl:text>
						</xsl:message>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="$node"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="content-templates"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="block.object">
		<xsl:call-template name="label.id"/>
		<xsl:apply-templates select="title"/>
		<xsl:text>
</xsl:text>
		<xsl:call-template name="content-templates"/>
	</xsl:template><xsl:template match="blockquote">
		<xsl:call-template name="map.begin"/>
		<xsl:apply-templates/>
		<xsl:apply-templates select="attribution" mode="block.attribution"/>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="epigraph">
		<xsl:call-template name="map.begin"/>
		<xsl:apply-templates/>
		<xsl:apply-templates select="attribution" mode="block.attribution"/>
		<xsl:call-template name="map.end"/>
	</xsl:template><xsl:template match="attribution"/><xsl:template match="attribution" mode="block.attribution">
		<xsl:text>
\hspace*\fill---</xsl:text>
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="sidebar">
		<xsl:call-template name="block.object"/>
	</xsl:template><xsl:template match="title|subtitle">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="title|subtitle" mode="caption.mode">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="ackno">
		<xsl:text>
</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template name="generate.latex.float.position">
		<xsl:param name="default" select="'hbt'"/>
		<xsl:choose>
			<xsl:when test="processing-instruction('latex-float-placement')">
				<xsl:value-of select="processing-instruction('latex-float-placement')"/>
			</xsl:when>
			<xsl:when test="starts-with(@condition, 'db2latex:')">
				<xsl:value-of select="substring-after(@condition, 'db2latex:')"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$default"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="generate.latex.width">
		<xsl:param name="width" select="normalize-space(@width)"/>
		<xsl:choose>
			<xsl:when test="contains($width, '%') and substring-after($width, '%')=''">
				<xsl:value-of select="number(substring-before($width, '%')) div 100"/>
				<xsl:text>\linewidth</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$width"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template></xsl:stylesheet>
