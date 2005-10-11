<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: revision.mod.xsl,v 1.8 2004/12/05 09:37:28 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

    <xsl:template match="revhistory">
	<!--
	<xsl:message>RCAS: Processing Revision History </xsl:message>
	-->
		<xsl:if test="$latex.output.revhistory=1">
			<xsl:call-template name="map.begin"/>
			<xsl:apply-templates/>
			<xsl:call-template name="map.end"/>
		</xsl:if>
	</xsl:template><xsl:template match="revision" name="revision">
		<xsl:param name="align" select="'l'"/>
		<xsl:variable name="revnumber" select=".//revnumber"/>
		<xsl:variable name="revdate" select=".//date"/>
		<xsl:variable name="revauthor" select=".//authorinitials"/>
		<xsl:variable name="revremark" select=".//revremark|.//revdescription"/>
		<!-- Row starts here -->
		<xsl:if test="$revnumber">
			<xsl:call-template name="gentext.element.name"/>
			<xsl:text> </xsl:text>
			<xsl:apply-templates select="$revnumber"/>
		</xsl:if>
		<xsl:text> &amp; </xsl:text>
		<xsl:apply-templates select="$revdate"/>
		<xsl:text> &amp; </xsl:text>
		<xsl:choose>
			<xsl:when test="count($revauthor)=0">
			<xsl:call-template name="dingbat">
				<xsl:with-param name="dingbat">nbsp</xsl:with-param>
			</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
			<xsl:apply-templates select="$revauthor"/>
			</xsl:otherwise>
		</xsl:choose>
		<!-- End Row here -->
		<xsl:text> \\ \hline
</xsl:text>
		<!-- Add Remark Row if exists-->
		<xsl:if test="$revremark"> 
			<xsl:text>\multicolumn{3}{|</xsl:text>
			<xsl:value-of select="$align"/>
			<xsl:text>|}{</xsl:text>
			<xsl:apply-templates select="$revremark"/> 
			<!-- End Row here -->
			<xsl:text>} \\ \hline
</xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="revision/authorinitials">
		<xsl:apply-templates/>
		<xsl:if test="following-sibling::authorinitials">
			<xsl:text>, </xsl:text>
		</xsl:if>
	</xsl:template><xsl:template match="revnumber">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="revision/date">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="revremark">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="revdescription">
		<xsl:apply-templates/>
	</xsl:template></xsl:stylesheet>
