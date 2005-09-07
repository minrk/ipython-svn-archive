<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: texmath.mod.xsl,v 1.12 2004/01/03 03:19:08 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="alt">
		<xsl:choose>
			<xsl:when test="ancestor::inlineequation and (@role='tex' or @role='latex' or $tex.math.in.alt='plain' or $tex.math.in.alt='latex')">
				<xsl:text>\ensuremath{</xsl:text>
				<xsl:value-of select="."/>
				<xsl:text>}</xsl:text>
			</xsl:when>
			<xsl:when test="(ancestor::equation|ancestor::informalequation) and (@role='tex' or @role='latex' or $tex.math.in.alt='plain' or $tex.math.in.alt='latex')">
				<xsl:text>\begin{displaymath}</xsl:text>
				<xsl:call-template name="label.id"/>
				<xsl:value-of select="."/>
				<xsl:text>\end{displaymath}
</xsl:text>
			</xsl:when>
			<xsl:when test="$tex.math.in.alt='plain' or $tex.math.in.alt='latex'">
				<xsl:value-of select="."/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="latex|tex">
		<xsl:value-of select="."/>
	</xsl:template><xsl:template match="latex[@fileref]|tex[@fileref]">
		<xsl:text>\input{</xsl:text><xsl:value-of select="@fileref"/><xsl:text>}
</xsl:text>
	</xsl:template><xsl:template match="tm[@fileref]">
		<xsl:text>\input{</xsl:text><xsl:value-of select="@fileref"/><xsl:text>}
</xsl:text>
	</xsl:template><xsl:template match="tm[@tex]">
		<xsl:value-of select="@tex"/>
	</xsl:template><xsl:template match="inlinetm[@fileref]">
		<xsl:text>\input{</xsl:text><xsl:value-of select="@fileref"/><xsl:text>}
</xsl:text>
	</xsl:template><xsl:template match="inlinetm[@tex]">
		<xsl:value-of select="@tex"/>
	</xsl:template><xsl:template match="inlineequation">
		<xsl:variable name="tex" select="alt[@role='tex' or @role='latex']|inlinemediaobject/textobject[@role='tex' or @role='latex']|inlinemediaobject/textobject/phrase[@role='tex' or @role='latex']"/>
		<xsl:choose>
			<xsl:when test="$tex">
				<xsl:apply-templates select="$tex"/>
			</xsl:when>
			<xsl:when test="alt and $latex.alt.is.preferred='1'">
				<xsl:apply-templates select="alt"/>
			</xsl:when>
			<xsl:when test="inlinemediaobject">
				<xsl:apply-templates select="inlinemediaobject"/>
			</xsl:when>
			<xsl:when test="alt">
				<xsl:apply-templates select="alt"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="graphic"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template></xsl:stylesheet>
