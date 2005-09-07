<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: normalize-scape.mod.xsl,v 1.33 2004/01/26 09:40:12 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
|														
|   PURPOSE:
|	Escape LaTeX and normalize-space templates.
|    < > # $ % & ~ _ ^ \ { } |
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:include href="scape.mod.xsl"/><xsl:template match="text()" name="text">
		<xsl:call-template name="trim-outer">
			<xsl:with-param name="string">
				<xsl:choose>
					<xsl:when test="ancestor::literal|ancestor::filename|ancestor::userinput|ancestor::systemitem|ancestor::prompt|ancestor::email|ancestor::sgmltag">
						<xsl:call-template name="scape-verbatim">
							<xsl:with-param name="string" select="."/>
						</xsl:call-template>
					</xsl:when>
					<xsl:otherwise>
						<xsl:call-template name="scape">
							<xsl:with-param name="string" select="."/>
						</xsl:call-template>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:with-param>
		</xsl:call-template>
	</xsl:template><!--
	<xsl:template match="abbrev/text()">
		<xsl:variable name="string">
			<xsl:call-template name="text"/>
		</xsl:variable>
		<xsl:call-template name="string-replace">
			<xsl:with-param name="to">.\ </xsl:with-param>
			<xsl:with-param name="from">. </xsl:with-param>
			<xsl:with-param name="string" select="$string"/>
		</xsl:call-template>
	</xsl:template>
	--><xsl:template match="text()" mode="xref.text">
		<xsl:call-template name="trim-outer">
			<xsl:with-param name="string">
				<xsl:call-template name="scape">
					<xsl:with-param name="string" select="."/>
				</xsl:call-template>
			</xsl:with-param>
		</xsl:call-template>
    </xsl:template><xsl:template match="text()" mode="xref-to">
		<xsl:call-template name="trim-outer">
			<xsl:with-param name="string">
				<xsl:call-template name="scape">
					<xsl:with-param name="string" select="."/>
				</xsl:call-template>
			</xsl:with-param>
		</xsl:call-template>
    </xsl:template><xsl:template match="text()" mode="latex.verbatim">
		<xsl:choose>
			<xsl:when test="$latex.trim.verbatim=1">
				<xsl:call-template name="trim.verbatim"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="."/> 
			</xsl:otherwise>
		</xsl:choose>
    </xsl:template><xsl:template match="text()" mode="slash.hyphen">
		<xsl:call-template name="trim-outer">
			<xsl:with-param name="string">
				<xsl:call-template name="scape.slash.hyphen">
					<xsl:with-param name="string" select="."/>
				</xsl:call-template>
			</xsl:with-param>
		</xsl:call-template>
	</xsl:template><xsl:template name="trim-outer">
		<xsl:param name="string"/>
		<xsl:variable name="trimleft" select="position()=1"/>
		<xsl:variable name="trimright" select="position()=last()"/>
		<xsl:choose>
			<xsl:when test="$trimleft and not($trimright)">
				<xsl:value-of select="substring-before(normalize-space(concat($string,'$$')),'$$')"/>
			</xsl:when>
			<xsl:when test="$trimright and not($trimleft)">
				<xsl:value-of select="substring-after(normalize-space(concat('$$',$string)),'$$')"/>
			</xsl:when>
			<xsl:when test="$trimleft and $trimright">
				<xsl:value-of select="normalize-space($string)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="substring-after(substring-before(normalize-space(concat('$$',$string,'$$$')),'$$$'),'$$')"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="scape.slash.hyphen">
	<xsl:param name="string"/>
	<xsl:choose>
		<xsl:when test="contains($string,'://')">
			<xsl:call-template name="scape-slash">
				<xsl:with-param name="string">
					<xsl:value-of select="substring-before($string,'://')"/>
					<xsl:value-of select="'://'"/>
					<xsl:call-template name="scape">
						<xsl:with-param name="string" select="substring-after($string,'://')"/>
					</xsl:call-template>
				</xsl:with-param>
			</xsl:call-template>
		</xsl:when>
		<xsl:otherwise>
			<xsl:call-template name="scape-slash">
				<xsl:with-param name="string">
					<xsl:call-template name="scape">
						<xsl:with-param name="string" select="$string"/>
					</xsl:call-template>
				</xsl:with-param>
			</xsl:call-template>
		</xsl:otherwise>
	</xsl:choose>
	</xsl:template><xsl:template name="normalize-scape">
		<xsl:param name="string"/>
		<xsl:variable name="result">
			<xsl:call-template name="scape">
				<xsl:with-param name="string" select="$string"/>
			</xsl:call-template>
		</xsl:variable>
		<xsl:value-of select="normalize-space($result)"/>
	</xsl:template><xsl:template name="string-replace">
		<xsl:param name="string"/>
		<xsl:param name="from"/>
		<xsl:param name="to"/>

		<xsl:choose>
			<xsl:when test="contains($string, $from)">

			<xsl:variable name="before" select="substring-before($string, $from)"/>
			<xsl:variable name="after" select="substring-after($string, $from)"/>
			<xsl:variable name="prefix" select="concat($before, $to)"/>

			<xsl:value-of select="$before"/>
			<xsl:value-of select="$to"/>
			<xsl:call-template name="string-replace">
				<xsl:with-param name="string" select="$after"/>
				<xsl:with-param name="from" select="$from"/>
				<xsl:with-param name="to" select="$to"/>
			</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
			<xsl:value-of select="$string"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--  
    (c) David Carlisle
    replace all occurences of the character(s) `from'
    by the string `to' in the string `string'.
    <xsl:template name="string-replace" >
	<xsl:param name="string"/>
	<xsl:param name="from"/>
	<xsl:param name="to"/>
	<xsl:choose>
	    <xsl:when test="contains($string,$from)">
		<xsl:value-of select="substring-before($string,$from)"/>
		<xsl:value-of select="$to"/>
		<xsl:call-template name="string-replace">
		    <xsl:with-param name="string" select="substring-after($string,$from)"/>
		    <xsl:with-param name="from" select="$from"/>
		    <xsl:with-param name="to" select="$to"/>
		</xsl:call-template>
	    </xsl:when>
	    <xsl:otherwise>
		<xsl:value-of select="$string"/>
	    </xsl:otherwise>
	</xsl:choose>
    </xsl:template>
    --><xsl:template name="trim.verbatim">
		<xsl:variable name="before" select="preceding-sibling::node()"/>
		<xsl:variable name="after" select="following-sibling::node()"/>

		<xsl:variable name="conts" select="."/>

		<xsl:variable name="contsl">
			<xsl:choose>
				<xsl:when test="count($before) = 0">
					<xsl:call-template name="remove-lf-left">
						<xsl:with-param name="astr" select="$conts"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$conts"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>

		<xsl:variable name="contslr">
			<xsl:choose>
				<xsl:when test="count($after) = 0">
					<xsl:call-template name="remove-ws-right">
						<xsl:with-param name="astr" select="$contsl"/>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$contsl"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>

		<xsl:value-of select="$contslr"/>
	</xsl:template><xsl:template name="remove-lf-left">
		<xsl:param name="astr"/>
		<xsl:choose>
			<xsl:when test="starts-with($astr,'&#10;') or                    starts-with($astr,'&#13;') or                    starts-with($astr,' ') or                    starts-with($astr,'&#9;')">
				<xsl:call-template name="remove-lf-left">
					<xsl:with-param name="astr" select="substring($astr, 2)"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$astr"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><xsl:template name="remove-ws-right">
		<xsl:param name="astr"/>
		<xsl:variable name="last-char">
			<xsl:value-of select="substring($astr, string-length($astr), 1)"/>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="($last-char = '&#10;') or                    ($last-char = '&#13;') or                    ($last-char = ' ') or                    ($last-char = '&#9;')">
				<xsl:call-template name="remove-ws-right">
					<xsl:with-param name="astr" select="substring($astr, 1, string-length($astr) - 1)"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$astr"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template></xsl:stylesheet>
