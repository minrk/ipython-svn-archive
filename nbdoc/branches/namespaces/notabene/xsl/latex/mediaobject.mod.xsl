<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: mediaobject.mod.xsl,v 1.25 2004/12/05 09:58:48 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="textobject">
		<!-- TODO if mixed in with imageobjects, use subfigure (if appropriate) -->
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="mediaobject|mediaobjectco">
		<xsl:if test="local-name(preceding-sibling::*[1])!='mediaobject' and local-name(preceding-sibling::*[1])!='mediaobjectco'">
			<xsl:text>
</xsl:text>
		</xsl:if>
		<xsl:call-template name="mediacontent"/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template match="para/mediaobject|para/mediaobjectco">
		<xsl:text>

</xsl:text>
		<xsl:call-template name="mediacontent"/>
		<xsl:text>

</xsl:text>
	</xsl:template><xsl:template match="inlinemediaobject">
		<xsl:call-template name="mediacontent"/>
	</xsl:template><xsl:template name="mediacontent">
		<!--
		<xsl:variable name="actualmediacnt" select="count(../../..//mediaobject[imageobject or textobject])"/>
		-->
		<xsl:variable name="actualmediacnt" select="count(../mediaobject)"/>
		<xsl:if test="$actualmediacnt &gt; 1 and $latex.use.subfigure='1' and count(ancestor::figure) &gt; 0">
			<xsl:text>\subfigure[</xsl:text>
			<!-- TODO does subfigure stuff up with there are square brackets in here? -->
			<xsl:if test="caption">
				<xsl:apply-templates select="caption[1]"/>
			</xsl:if>
			<xsl:text>]</xsl:text>
		</xsl:if>
		<xsl:text>{</xsl:text>
		<xsl:choose>
			<xsl:when test="count(imageobject|imageobjectco)&lt;1">
				<xsl:apply-templates select="textobject[1]"/>
			</xsl:when>
			<xsl:when test="$use.role.for.mediaobject='1' and $preferred.mediaobject.role!='' and count((imageobject|imageobjectco)[@role=$preferred.mediaobject.role])!=0">
				<xsl:apply-templates select="(imageobject|imageobjectco)[@role=$preferred.mediaobject.role]"/>
			</xsl:when>
			<xsl:when test="$use.role.for.mediaobject='1' and count((imageobject|imageobjectco)[@role='latex'])!=0">
				<xsl:apply-templates select="(imageobject|imageobjectco)[@role='latex']"/>
			</xsl:when>
			<xsl:when test="$use.role.for.mediaobject='1' and count((imageobject|imageobjectco)[@role='tex'])!=0">
				<xsl:apply-templates select="(imageobject|imageobjectco)[@role='tex']"/>
			</xsl:when>
			<xsl:when test="$latex.graphics.formats!='' and count((imageobject|imageobjectco)/imagedata[@format!=''])!=0">
				<!-- this is not really the right method: formats to the left of $latex.graphics.formats
				should be given higher 'priority' than those to the right in a command-separated list -->
				<xsl:variable name="formats" select="concat(',',$latex.graphics.formats,',')"/>
				<xsl:variable name="candidates" select="(imageobject|imageobjectco)/imagedata[contains($formats,concat(',',@format,','))]"/>
				<xsl:choose>
					<xsl:when test="count($candidates)!=0">
						<xsl:apply-templates select="$candidates[1]"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:variable name="fallbacks" select="(imageobject|imageobjectco)/imagedata[@format='' or not(@format)]"/>
						<xsl:choose>
							<xsl:when test="count($fallbacks)!=0">
								<xsl:apply-templates select="$fallbacks[1]"/>
							</xsl:when>
							<xsl:when test="count(textobject)!=0">
								<xsl:apply-templates select="textobject[1]"/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:apply-templates select="(imageobject|imageobjectco)[1]"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="(imageobject|imageobjectco)[1]"/>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:text>}</xsl:text>
	</xsl:template><xsl:template match="imageobject">
		<xsl:apply-templates select="imagedata"/>
	</xsl:template><xsl:template match="imagedata" name="imagedata">
		<xsl:param name="filename">
			<xsl:choose>
				<xsl:when test="@entityref">
					<xsl:value-of select="unparsed-entity-uri(@entityref)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="@fileref"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:param>
		<xsl:param name="is.imageobjectco" select="false()"/>
		<xsl:variable name="depth" select="normalize-space(@depth)"/>
		<xsl:variable name="width">
			<xsl:call-template name="generate.latex.width"/>
		</xsl:variable>
		<xsl:if test="$width!='' and (@scalefit='0' or count(@scale)&gt;0)">
			<xsl:text>\makebox[</xsl:text><xsl:value-of select="$width"/><xsl:text>]</xsl:text>
		</xsl:if>
		<!-- TODO this logic actually needs to make decisions based on the ALLOWED imagedata,
		not all the imagedata present in the source file. -->
		<xsl:choose>
			<xsl:when test="$is.imageobjectco=1">
				<xsl:text>{\begin{overpic}[</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>{\includegraphics[</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:choose>
			<xsl:when test="@scale"> 
			<xsl:text>scale=</xsl:text>
			<xsl:value-of select="number(@scale) div 100"/>
			</xsl:when>
			<xsl:when test="$width!='' and @scalefit='1'">
			<xsl:text>width=</xsl:text><xsl:value-of select="normalize-space($width)"/>
			</xsl:when>
			<xsl:when test="$depth!='' and @scalefit='1'">
			<xsl:text>height=</xsl:text><xsl:value-of select="$depth"/>
			</xsl:when>
		</xsl:choose>
		<xsl:choose>
			<xsl:when test="@format = 'PRN'"><xsl:text>,angle=270</xsl:text></xsl:when>
		</xsl:choose>
		<xsl:text>]{</xsl:text>
		<xsl:value-of select="$filename"/>
		<xsl:choose>
			<xsl:when test="$is.imageobjectco=1">
				<xsl:text>}
\calsscale
</xsl:text>
				<xsl:apply-templates select="ancestor::imageobjectco/areaspec//area"/>
				<xsl:text>\end{overpic}}</xsl:text>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>}}</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="caption">
		<xsl:apply-templates/>
	</xsl:template></xsl:stylesheet>
