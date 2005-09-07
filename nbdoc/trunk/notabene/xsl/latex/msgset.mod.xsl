<?xml version="1.0"?>
<!--############################################################################# 
|	$Id: msgset.mod.xsl,v 1.2 2004/01/01 14:04:58 j-devenish Exp $
|- #############################################################################
|	$Author: j-devenish $
+ ############################################################################## -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" exclude-result-prefixes="doc" version="1.0">

	<xsl:template match="msgset">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="msgentry">
		<xsl:call-template name="block.object"/>
	</xsl:template><xsl:template match="simplemsgentry">
		<xsl:call-template name="block.object"/>
	</xsl:template><xsl:template match="msg">
		<xsl:call-template name="block.object"/>
	</xsl:template><xsl:template match="msgmain">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="msgmain/title|msgsub/title|msgrel/title">
		<xsl:text>{\textbf{</xsl:text>
		<xsl:apply-templates/>
		<xsl:text>}} </xsl:text>
	</xsl:template><xsl:template match="msgsub">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="msgrel">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="msgtext">
		<xsl:apply-templates/>
	</xsl:template><xsl:template match="msginfo">
		<xsl:call-template name="block.object"/>
	</xsl:template><!-- localised --><xsl:template match="msglevel|msgorig|msgaud">
		<xsl:text>
</xsl:text>
		<xsl:text>{\textbf{</xsl:text>
		<xsl:call-template name="gentext.element.name"/>
		<xsl:text>: </xsl:text>
		<xsl:text>}} </xsl:text>
		<xsl:apply-templates/>
		<xsl:text>
</xsl:text>
	</xsl:template><xsl:template match="msgexplan">
		<xsl:call-template name="block.object"/>
	</xsl:template></xsl:stylesheet>
