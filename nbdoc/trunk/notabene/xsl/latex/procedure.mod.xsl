<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: procedure.mod.xsl,v 1.14 2004/08/17 07:15:53 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="procedure" name="procedure">
		<xsl:param name="mode" select="''"/>
		<xsl:param name="environment">
			<xsl:choose>
				<xsl:when test="$mode='custom'">
					<xsl:text>description</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>enumerate</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:variable name="placement">
			<xsl:call-template name="generate.formal.title.placement">
				<xsl:with-param name="object" select="local-name(.)"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:variable name="preamble" select="node()[not(self::blockinfo or self::title or self::subtitle or self::titleabbrev or self::step)]"/>
		<xsl:choose>
			<xsl:when test="$placement='before' or $placement=''">
				<xsl:apply-templates select="title"/>
				<xsl:apply-templates select="$preamble"/>
				<xsl:text>\begin{</xsl:text>
				<xsl:value-of select="$environment"/>
				<xsl:text>}
</xsl:text>
				<xsl:apply-templates select="step">
					<xsl:with-param name="mode" select="$mode"/>
				</xsl:apply-templates>
				<xsl:text>\end{</xsl:text>
				<xsl:value-of select="$environment"/>
				<xsl:text>}
</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="$preamble"/>
				<xsl:text>\begin{</xsl:text>
				<xsl:value-of select="$environment"/>
				<xsl:text>}
</xsl:text>
				<xsl:apply-templates select="step">
					<xsl:with-param name="mode" select="$mode"/>
				</xsl:apply-templates>
				<xsl:text>\end{</xsl:text>
				<xsl:value-of select="$environment"/>
				<xsl:text>}
</xsl:text>
				<xsl:apply-templates select="title"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="procedure/title">
		<xsl:text>

{</xsl:text>
		<xsl:value-of select="$latex.procedure.title.style"/>
		<xsl:text>{</xsl:text>
		<xsl:choose>
			<xsl:when test="$latex.apply.title.templates=1">
				<xsl:apply-templates/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="."/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:text>}}</xsl:text>
		<xsl:call-template name="label.id">
			<xsl:with-param name="object" select=".."/>
		</xsl:call-template>
		<xsl:text>\hypertarget{</xsl:text>
		<xsl:call-template name="generate.label.id">
			<xsl:with-param name="object" select=".."/>
		</xsl:call-template>
		<xsl:text>}{}
</xsl:text>
	</xsl:template><xsl:template match="step" name="step">
		<xsl:param name="mode" select="''"/>
		<xsl:param name="title">
			<xsl:call-template name="generate.step.title">
				<xsl:with-param name="mode" select="$mode"/>
			</xsl:call-template>
		</xsl:param>
		<xsl:choose>
			<xsl:when test="$title!='' and $mode='custom'">
				<xsl:text>
\item[{</xsl:text>
				<xsl:value-of select="$latex.step.title.style"/> <!-- by default \sc -->
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$title"/>
				<xsl:text>}}]
{</xsl:text>
			</xsl:when>
			<xsl:when test="$title!=''">
				<xsl:text>
\item{{</xsl:text>
				<xsl:value-of select="$latex.step.title.style"/> <!-- by default \sc -->
				<xsl:text>{</xsl:text>
				<xsl:value-of select="$title"/>
				<xsl:text>}}
</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>
\item{</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		 <xsl:apply-templates select="node()[not(self::title)]"/>
		<xsl:text>}
</xsl:text>
	</xsl:template><xsl:template name="generate.step.title">
		<xsl:param name="mode"/>
		<xsl:choose>
			<xsl:when test="title">
				<xsl:apply-templates select="title"/>
			</xsl:when>
			<xsl:when test="$mode='custom'">
				<xsl:number format="1."/>
			</xsl:when>
			<!-- otherwise, empty -->
		</xsl:choose>
	</xsl:template><xsl:template match="substeps">
		<xsl:param name="mode" select="''"/>
		<xsl:param name="environment">
			<xsl:choose>
				<xsl:when test="$mode='custom'">
					<xsl:text>description</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<xsl:text>enumerate</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:text>\begin{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}
</xsl:text>
		<xsl:apply-templates select="step">
			<xsl:with-param name="mode" select="$mode"/>
		</xsl:apply-templates>
		<xsl:text>\end{</xsl:text>
		<xsl:value-of select="$environment"/>
		<xsl:text>}
</xsl:text>
	</xsl:template></xsl:stylesheet>
