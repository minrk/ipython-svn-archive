<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: email.mod.xsl,v 1.6 2003/12/28 10:43:16 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="email">
		<xsl:call-template name="ulink">
			<xsl:with-param name="url" select="concat('mailto:',.)"/>
			<xsl:with-param name="content" select="."/>
		</xsl:call-template>
	</xsl:template></xsl:stylesheet>
