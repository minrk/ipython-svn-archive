<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: authorgroup.mod.xsl,v 1.10 2003/12/30 13:38:54 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $												
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="authorgroup" name="authorgroup">
		<xsl:param name="person.list" select="./author|./corpauthor|./othercredit|./editor"/>
		<xsl:call-template name="normalize-scape">
			<xsl:with-param name="string">
				<xsl:call-template name="person.name.list">
					<xsl:with-param name="person.list" select="$person.list"/>
				</xsl:call-template>
			</xsl:with-param>
		</xsl:call-template>
	</xsl:template><xsl:template match="author|editor|othercredit|personname">
		<xsl:call-template name="normalize-scape">
			<xsl:with-param name="string">
				<xsl:call-template name="person.name"/>
			</xsl:with-param>
		</xsl:call-template>
	</xsl:template><xsl:template match="authorinitials">
		<xsl:apply-templates/>
		<xsl:value-of select="$biblioentry.item.separator"/>
	</xsl:template></xsl:stylesheet>
