<?xml version="1.0"?>
<!--#############################################################################
|      $Id: latex.mapping.xsl,v 1.18 2004/01/14 14:54:32 j-devenish Exp $
|- #############################################################################
|      $Author: j-devenish $
|
|   PURPOSE:
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<!--############################################################################# --><!-- DOCUMENTATION                                                                --><!--############################################################################# --><xsl:param name="latex.mapping.xml" select="document('latex.mapping.xml')"/><xsl:param name="latex.mapping.xml.default" select="document('latex.mapping.xml')"/><xsl:template name="latex.mapping">
		<xsl:param name="object" select="."/>
		<xsl:param name="keyword" select="local-name($object)"/>
		<xsl:param name="role" select="begin"/>
		<xsl:param name="string">
			<xsl:call-template name="extract.object.title">
				<xsl:with-param name="object" select="$object"/>
			</xsl:call-template>
		</xsl:param>
		<xsl:variable name="id">
			<xsl:call-template name="generate.label.id">
				<xsl:with-param name="object" select="$object"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="title">
			<xsl:choose>
			<xsl:when test="starts-with(local-name($object),'informal')">
				<xsl:if test="$string!=''">
					<xsl:message>Ignoring title for <xsl:value-of select="local-name($object)"/>.</xsl:message>
				</xsl:if>
			</xsl:when>
			<xsl:when test="$string=''">
				<xsl:call-template name="gentext.element.name"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="normalize-space($string)"/>
			</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="local.mapping" select="$latex.mapping.xml/latexbindings/latexmapping[@role=$role]/mapping[@key=$keyword]"/>
		<xsl:variable name="default.mapping" select="$latex.mapping.xml.default/latexbindings/latexmapping[@role=$role]/mapping[@key=$keyword]"/>
		
		<xsl:choose>
			<xsl:when test="$local.mapping and ($local.mapping/@text!='' or not($local.mapping/line))">
				<xsl:call-template name="string-replace">
					<xsl:with-param name="to"><xsl:value-of select="$id"/></xsl:with-param>
					<xsl:with-param name="from">%id%</xsl:with-param>
					<xsl:with-param name="string">
						<xsl:call-template name="string-replace">
							<xsl:with-param name="to"><xsl:value-of select="$title"/></xsl:with-param>
							<xsl:with-param name="from">%title%</xsl:with-param>
							<xsl:with-param name="string">
								<xsl:value-of select="$local.mapping/@text"/>
							</xsl:with-param>
						</xsl:call-template>
					</xsl:with-param>
				</xsl:call-template>
			</xsl:when>

			<xsl:when test="$local.mapping/line">
				<xsl:for-each select="$local.mapping/line">
					<xsl:call-template name="string-replace">
						<xsl:with-param name="to"><xsl:value-of select="$id"/></xsl:with-param>
						<xsl:with-param name="from">%id%</xsl:with-param>
						<xsl:with-param name="string">
							<xsl:call-template name="string-replace">
								<xsl:with-param name="to"><xsl:value-of select="$title"/></xsl:with-param>
								<xsl:with-param name="from">%title%</xsl:with-param>
								<xsl:with-param name="string" select="."/>
							</xsl:call-template>
						</xsl:with-param>
					</xsl:call-template>
				</xsl:for-each>
			</xsl:when>

			<xsl:when test="$default.mapping/@text!=''">
				<xsl:call-template name="string-replace">
					<xsl:with-param name="to"><xsl:value-of select="$id"/></xsl:with-param>
					<xsl:with-param name="from">%id%</xsl:with-param>
					<xsl:with-param name="string">
						<xsl:call-template name="string-replace">
							<xsl:with-param name="to"><xsl:value-of select="$title"/></xsl:with-param>
							<xsl:with-param name="from">%title%</xsl:with-param>
							<xsl:with-param name="string">
								<xsl:value-of select="$default.mapping/@text"/>
							</xsl:with-param>
						</xsl:call-template>
					</xsl:with-param>
				</xsl:call-template>
			</xsl:when>

			<xsl:when test="$default.mapping">
			<xsl:for-each select="$default.mapping/line">
				<xsl:call-template name="string-replace">
					<xsl:with-param name="to"><xsl:value-of select="$id"/></xsl:with-param>
					<xsl:with-param name="from">%id%</xsl:with-param>
					<xsl:with-param name="string">
						<xsl:call-template name="string-replace">
							<xsl:with-param name="to"><xsl:value-of select="$title"/></xsl:with-param>
							<xsl:with-param name="from">%title%</xsl:with-param>
							<xsl:with-param name="string" select="."/>
						</xsl:call-template>
					</xsl:with-param>
				</xsl:call-template>
			</xsl:for-each>

			</xsl:when>
				<xsl:otherwise>
					<xsl:message terminate="no">
						<xsl:text>Warning: Unable to find LaTeX mapping for 
</xsl:text>
						<xsl:text>KEYWORD:</xsl:text><xsl:value-of select="$keyword"/><xsl:text>
</xsl:text>
						<xsl:text>ROLE:</xsl:text><xsl:value-of select="$role"/><xsl:text>
</xsl:text>
					</xsl:message>
				</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="map.begin">
	<xsl:param name="object" select="."/>
	<xsl:param name="keyword" select="local-name($object)"/>
	<xsl:param name="string">
		<xsl:call-template name="extract.object.title">
			<xsl:with-param name="object" select="$object"/>
		</xsl:call-template>
	</xsl:param>
	<xsl:call-template name="latex.mapping">
	    <xsl:with-param name="keyword" select="$keyword"/>
	    <xsl:with-param name="role">begin</xsl:with-param>
	    <xsl:with-param name="string" select="$string"/>
	</xsl:call-template>
    </xsl:template><xsl:template name="map.end">
	<xsl:param name="object" select="."/>
	<xsl:param name="keyword" select="local-name($object)"/>
	<xsl:param name="role" select="begin"/>
	<xsl:param name="string">
		<xsl:call-template name="extract.object.title">
			<xsl:with-param name="object" select="$object"/>
		</xsl:call-template>
	</xsl:param>
	<xsl:call-template name="latex.mapping">
	    <xsl:with-param name="keyword" select="$keyword"/>
	    <xsl:with-param name="string" select="$string"/>
	    <xsl:with-param name="role">end</xsl:with-param>
	</xsl:call-template>
    </xsl:template><xsl:template name="extract.object.title">
		<xsl:param name="object" select="."/>
		<xsl:choose>
			<xsl:when test="$latex.apply.title.templates='1'">
				<xsl:apply-templates select="$object/title" mode="latex"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="normalize-scape">
					<xsl:with-param name="string" select="$object/title"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="title" mode="latex"><xsl:apply-templates/></xsl:template></xsl:stylesheet>
