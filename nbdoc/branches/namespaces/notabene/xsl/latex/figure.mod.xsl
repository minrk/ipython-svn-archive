<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: figure.mod.xsl,v 1.18 2004/08/12 05:28:37 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $												
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template name="generate.aux.figure.caption">
		<xsl:text>{</xsl:text>
		<xsl:value-of select="$latex.figure.caption.style"/>
		<xsl:choose>
			<xsl:when test="$latex.caption.lot.titles.only='1'">
				<xsl:text>{\caption[{</xsl:text>
				<xsl:apply-templates select="title"/>
				<xsl:text>}]{{</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>{\caption{{</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:value-of select="$latex.figure.title.style"/>
		<xsl:text>{</xsl:text>
		<xsl:apply-templates select="title"/>
		<xsl:text>}}</xsl:text>
		<xsl:if test="count(child::mediaobject/caption|child::mediaobjectco/caption)=1">
			<xsl:text>. </xsl:text>
			<xsl:apply-templates select="mediaobject/caption|child::mediaobjectco/caption"/>
		</xsl:if>
		<xsl:text>}</xsl:text>
		<xsl:call-template name="label.id"/>
		<xsl:text>}}
</xsl:text>
	</xsl:template><xsl:template match="figure">
		<xsl:variable name="placement">
			<xsl:call-template name="generate.formal.title.placement">
				<xsl:with-param name="object" select="local-name(.)"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="position">
			<xsl:call-template name="generate.latex.float.position">
				<xsl:with-param name="default" select="'hbt'"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:call-template name="map.begin">
			<xsl:with-param name="string" select="$position"/>
		</xsl:call-template>
		<xsl:if test="$placement='before'">
			<xsl:text>\captionswapskip{}</xsl:text>
			<xsl:call-template name="generate.aux.figure.caption"/>
			<xsl:text>\captionswapskip{}</xsl:text>
		</xsl:if>
		<xsl:apply-templates select="*[name(.) != 'title']"/>
		<xsl:if test="$placement!='before'">
			<xsl:call-template name="generate.aux.figure.caption"/>
		</xsl:if>
		<xsl:call-template name="map.end">
			<xsl:with-param name="string" select="$position"/>
		</xsl:call-template>
	</xsl:template><xsl:template name="generate.aux.informalfigure.caption">
		<xsl:if test="count(child::mediaobject/caption|child::mediaobjectco/caption)=1">
			<xsl:text>\begin{center}
</xsl:text>
			<xsl:apply-templates select="mediaobject/caption|child::mediaobjectco/caption"/>
			<xsl:text>\end{center}
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="informalfigure">
		<xsl:call-template name="map.begin"/>
		<xsl:apply-templates/>
		<xsl:call-template name="generate.aux.informalfigure.caption"/>
		<xsl:call-template name="map.end"/>
	</xsl:template><!--
    <xsl:template match="figure[programlisting]">
	<xsl:call-template name="map.begin">
	    <xsl:with-param name="keyword" select="programlisting"/>
	</xsl:call-template>
	<xsl:apply-templates />
	<xsl:call-template name="map.end">
	    <xsl:with-param name="keyword" select="programlisting"/>
	</xsl:call-template>
    </xsl:template>
	--></xsl:stylesheet>
