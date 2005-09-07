<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: bridgehead.mod.xsl,v 1.12 2004/01/11 11:35:25 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="bridgehead" name="bridgehead">
		<xsl:param name="renderas" select="@renderas"/>
		<xsl:param name="content"><xsl:apply-templates/></xsl:param>
		<xsl:choose>
			<xsl:when test="$renderas='sect1' or $renderas='sect2' or $renderas='sect3'">
				<xsl:text>
\</xsl:text>
				<xsl:if test="$renderas='sect2'"><xsl:text>sub</xsl:text></xsl:if>
				<xsl:if test="$renderas='sect3'"><xsl:text>subsub</xsl:text></xsl:if>
				<xsl:text>section*{</xsl:text>
				<xsl:copy-of select="$content"/>
				<xsl:text>}</xsl:text>
				<xsl:call-template name="label.id"/>
				<xsl:text>
</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<!--
				<xsl:text>&#10;&#10;</xsl:text>
				<xsl:text>\vspace{1em}\noindent{\bfseries </xsl:text><xsl:copy-of select="$content"/><xsl:text>}</xsl:text>
				<xsl:call-template name="label.id"/>
				<xsl:text>\par\noindent&#10;</xsl:text>
				-->
				<xsl:text>
\paragraph*{</xsl:text>
				<xsl:copy-of select="$content"/>
				<xsl:text>}</xsl:text>
				<xsl:call-template name="label.id"/>
				<xsl:text>

\noindent
</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template></xsl:stylesheet>
