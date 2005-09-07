<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: callout.mod.xsl,v 1.11 2004/08/12 06:25:52 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template name="latex.preamble.essential.callout">
		<xsl:if test="$latex.use.overpic=1 and //areaspec">
			<xsl:text>
				
\usepackage[percent]{overpic}
\newdimen\dblatex@ascale \newdimen\dblatex@bscale
\newdimen\dblatex@adimen \newdimen\dblatex@bdimen
\newdimen\dblatex@cdimen \newdimen\dblatex@ddimen
\newcommand{\calsscale}{%
   \ifnum\@tempcnta&gt;\@tempcntb%
      \dblatex@ascale=1pt%
      \dblatex@bscale=\@tempcntb pt%
      \divide\dblatex@bscale by \@tempcnta%
   \else%
      \dblatex@bscale=1 pt%
      \dblatex@ascale=\@tempcnta pt%
      \divide\dblatex@ascale by \@tempcntb%
   \fi%
}
\newcommand{\calspair}[3]{
   \sbox{\z@}{#3}
   \settowidth{\dblatex@cdimen}{\usebox{\z@}}
   \settoheight{\dblatex@ddimen}{\usebox{\z@}}
   \divide\dblatex@cdimen by 2
   \divide\dblatex@ddimen by 2
   \dblatex@adimen=#1 pt \dblatex@adimen=\strip@pt\dblatex@ascale\dblatex@adimen
   \dblatex@bdimen=#2 pt \dblatex@bdimen=\strip@pt\dblatex@bscale\dblatex@bdimen
   \put(\strip@pt\dblatex@adimen,\strip@pt\dblatex@bdimen){\hspace{-\dblatex@cdimen}\raisebox{-\dblatex@ddimen}{\usebox{\z@}}}
}

			</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="programlistingco|screenco">
		<xsl:apply-templates select="programlisting|screen|calloutlist"/>
	</xsl:template><xsl:template match="areaspec|areaset"/><xsl:template match="co">
		<xsl:variable name="conum">
			<xsl:number count="co" format="1"/>
		</xsl:variable>
		<xsl:text>(</xsl:text>
		<xsl:value-of select="$conum"/>
		<xsl:text>)</xsl:text>
	</xsl:template><xsl:template match="calloutlist">
		<xsl:apply-templates select="./title"/>
		<xsl:text>
\begin{description}
</xsl:text>
		<xsl:apply-templates select="callout"/>
		<xsl:text>\end{description}
</xsl:text>
	</xsl:template><xsl:template match="calloutlist/title">
		<xsl:param name="style" select="$latex.list.title.style"/>
		<xsl:text>
{</xsl:text>
		<xsl:value-of select="$style"/>
		<xsl:text>{</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>}}
</xsl:text>
	</xsl:template><xsl:template match="callout">
		<xsl:text>\item[{</xsl:text>
		<xsl:call-template name="generate.callout.arearefs"/>
		<xsl:text>}]\null{}
</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template name="generate.callout.arearefs">
		<xsl:param name="arearefs" select="normalize-space(@arearefs)"/>
		<xsl:param name="count" select="1"/>
		<xsl:if test="$arearefs!=''">
			<xsl:choose>
				<xsl:when test="substring-before($arearefs,' ')=''">
					<xsl:apply-templates select="." mode="generate.callout.arearef">
						<xsl:with-param name="arearef" select="$arearefs"/>
						<xsl:with-param name="count" select="$count"/>
						<xsl:with-param name="last" select="true()"/>
					</xsl:apply-templates>
				</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="." mode="generate.callout.arearef">
						<xsl:with-param name="arearef" select="substring-before($arearefs,' ')"/>
						<xsl:with-param name="count" select="$count"/>
						<xsl:with-param name="last" select="false()"/>
					</xsl:apply-templates>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:call-template name="generate.callout.arearefs">
				<xsl:with-param name="arearefs" select="substring-after($arearefs,' ')"/>
				<xsl:with-param name="count" select="$count + 1"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template><xsl:template match="callout" mode="generate.callout.arearef">
		<xsl:param name="arearef" select="@arearefs"/>
		<xsl:param name="area" select="key('id', $arearef)"/>
		<xsl:param name="last" select="false()"/>
		<xsl:param name="count" select="1"/>
		<xsl:variable name="first" select="$count=1"/>
		<xsl:choose>
			<xsl:when test="$first">
				<xsl:call-template name="gentext.template">
					<xsl:with-param name="context" select="'naturalinlinelist'"/>
					<xsl:with-param name="name" select="'start'"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$last">
				<xsl:call-template name="gentext.template">
					<xsl:with-param name="context" select="'naturalinlinelist'"/>
					<xsl:with-param name="name">
						<xsl:choose>
							<xsl:when test="$count &gt; 2">
								<xsl:text>lastofmany</xsl:text>
							</xsl:when>
							<xsl:otherwise>
								<xsl:text>lastoftwo</xsl:text>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:with-param>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="gentext.template">
					<xsl:with-param name="context" select="'naturalinlinelist'"/>
					<xsl:with-param name="name" select="'middle'"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:choose>
			<xsl:when test="$area">
				<xsl:apply-templates select="$area" mode="generate.area.arearef"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>?</xsl:text>
				<xsl:message>
					<xsl:text>Error: no ID for constraint arearefs: </xsl:text>
					<xsl:value-of select="$arearef"/>
					<xsl:text>.</xsl:text>
				</xsl:message>
			</xsl:otherwise>
		</xsl:choose>
		<xsl:if test="$last">
			<xsl:call-template name="gentext.template">
				<xsl:with-param name="context" select="'naturalinlinelist'"/>
				<xsl:with-param name="name" select="'end'"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template><xsl:template match="area" mode="generate.area.arearef">
		<xsl:variable name="units">
			<xsl:choose>
				<xsl:when test="@units!=''">
					<xsl:value-of select="@units"/>
				</xsl:when>
				<xsl:when test="../@units!=''">
					<xsl:value-of select="../@units"/>
				</xsl:when>
				<xsl:when test="../../@units!=''">
					<xsl:value-of select="../../@units"/>
				</xsl:when>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="$units='calspair'">
				<xsl:apply-templates select="." mode="generate.arearef.calspair"/>
			</xsl:when>
			<xsl:when test="$units='linerange'">
				<xsl:apply-templates select="." mode="generate.arearef.linerange"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="." mode="generate.arearef">
					<xsl:with-param name="units" select="$units"/>
				</xsl:apply-templates>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="area" mode="generate.arearef">
		<xsl:param name="units"/>
		<xsl:message>Error: unsupported arearef units <xsl:value-of select="$units"/>.</xsl:message>
	</xsl:template><xsl:template match="area" mode="generate.arearef.calspair">
		<xsl:apply-templates select="." mode="generate.area.areasymbol"/>
	</xsl:template><xsl:template match="area" mode="generate.arearef.linerange">
		<xsl:choose>
			<xsl:when test="not(contains(@coords, ' '))">
				<xsl:value-of select="@coords"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="start" select="substring-before(@coords, ' ')"/>
				<xsl:variable name="finish" select="substring-after(@coords, ' ')"/>
				<xsl:choose>
					<xsl:when test="$start=$finish">
						<xsl:value-of select="$start"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:call-template name="string-replace">
							<xsl:with-param name="from" select="' '"/>
							<xsl:with-param name="to" select="'--'"/>
							<xsl:with-param name="string" select="@coords"/>
						</xsl:call-template>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="area">
		<xsl:apply-templates select="." mode="generate.area.areamark"/>
	</xsl:template><xsl:template match="area" mode="generate.area.areamark">
		<xsl:variable name="units">
			<xsl:choose>
				<xsl:when test="@units!=''">
					<xsl:value-of select="@units"/>
				</xsl:when>
				<xsl:when test="../@units!=''">
					<xsl:value-of select="../@units"/>
				</xsl:when>
				<xsl:when test="../../@units!=''">
					<xsl:value-of select="../../@units"/>
				</xsl:when>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="$units='calspair'">
				<xsl:apply-templates select="." mode="generate.areamark.calspair"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="." mode="generate.areamark">
					<xsl:with-param name="units" select="$units"/>
				</xsl:apply-templates>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="area" mode="generate.areamark">
		<xsl:param name="units"/>
		<xsl:message>Error: unsupported areamark units <xsl:value-of select="$units"/>.</xsl:message>
	</xsl:template><xsl:template match="area" mode="generate.areamark.calspair">
		<xsl:choose>
			<xsl:when test="not(contains(@coords, ' '))">
				<xsl:message>Error: invalid calspair '<xsl:value-of select="@coords"/>'.</xsl:message>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="x1y1">
					<xsl:value-of select="substring-before(@coords, ' ')"/>
				</xsl:variable>
				<xsl:variable name="x1">
					<xsl:choose>
						<xsl:when test="contains($x1y1, ',')">
							<xsl:value-of select="substring-before($x1y1, ',')"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="$x1y1"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:variable name="y1">
					<xsl:choose>
						<xsl:when test="contains($x1y1, ',')">
							<xsl:value-of select="substring-after($x1y1, ',')"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="''"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:variable name="x2y2">
					<xsl:value-of select="substring-after(@coords, ' ')"/>
				</xsl:variable>
				<xsl:variable name="y2">
					<xsl:choose>
						<xsl:when test="contains($x2y2, ',')">
							<xsl:value-of select="substring-after($x2y2, ',')"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="$x2y2"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:variable name="x2">
					<xsl:choose>
						<xsl:when test="contains($x2y2, ',')">
							<xsl:value-of select="substring-before($x2y2, ',')"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="''"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:text>\calspair{</xsl:text>
				<!-- choose horizontal coordinate -->
				<xsl:choose>
					<xsl:when test="$x1 != '' and $x2 != ''">
						<xsl:value-of select="(number($x1)+number($x2)) div 200"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="number(concat($x1, $x2)) div 100"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>}{</xsl:text>
				<!-- choose vertical coordinate -->
				<xsl:choose>
					<xsl:when test="$y1 != '' and $y2 != ''">
						<xsl:value-of select="(number($y1)+number($y2)) div 200"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="number(concat($y1, $y2)) div 100"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:text>}{</xsl:text>
				<xsl:apply-templates select="." mode="generate.area.areasymbol"/>
				<xsl:text>}
</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="area" mode="generate.area.areasymbol">
		<xsl:param name="linkends" select="normalize-space(@linkends)"/>
		<xsl:choose>
			<xsl:when test="@label">
				<xsl:value-of select="@label"/>
			</xsl:when>
			<xsl:when test="$linkends!=''">
				<xsl:variable name="linkend">
					<xsl:choose>
						<xsl:when test="contains($linkends, ' ')">
							<xsl:value-of select="substring-before($linkends, ' ')"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="$linkends"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:variable name="target" select="key('id', $linkend)"/>
				<xsl:choose>
					<xsl:when test="count($target)&gt;0">
						<xsl:for-each select="$target">
							<xsl:apply-templates select="." mode="generate.callout.areasymbol">
								<xsl:with-param name="arearef" select="generate-id(current())"/>
								<xsl:with-param name="area" select="current()"/>
							</xsl:apply-templates>
						</xsl:for-each>
					</xsl:when>
					<xsl:otherwise>
						<xsl:text>?</xsl:text>
						<xsl:message>
							<xsl:text>Error: no ID for constraint linkends: </xsl:text>
							<xsl:value-of select="$linkends"/>
							<xsl:text>.</xsl:text>
						</xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:text>*</xsl:text>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template match="*" mode="generate.callout.areasymbol">
		<xsl:call-template name="generate.hyperlink">
			<xsl:with-param name="target" select="."/>
			<xsl:with-param name="text">
				<xsl:call-template name="generate.xref.text">
					<xsl:with-param name="target" select="."/>
					<xsl:with-param name="xrefstyle" select="'xref-callout'"/>
				</xsl:call-template>
			</xsl:with-param>
		</xsl:call-template>
	</xsl:template><xsl:template match="callout" mode="generate.callout.areasymbol">
		<xsl:number count="callout" format="1"/>
	</xsl:template><xsl:template match="imageobjectco">
		<xsl:apply-templates select="imageobject"/>
		<xsl:text>
</xsl:text>
		<xsl:apply-templates select="calloutlist"/>
	</xsl:template><xsl:template match="imageobjectco/imageobject">
		<xsl:apply-templates select="imagedata">
			<xsl:with-param name="is.imageobjectco" select="true()"/>
		</xsl:apply-templates>
	</xsl:template></xsl:stylesheet>
