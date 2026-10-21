///*	**************************************************************************************************************************************		*///
///*	杭州科澜信息技术有限公司	http://www.hzkelan.com																									*///
///*	版权所有 (c) 2006 - 2013																																			*///
///*	**************************************************************************************************************************************		*///
///*	文件名		：		Util.h																																				*///
///*	功能说明	：		应用工具																																		*///
///*	文件摘要	：																																							*///
///*	其		他		：																																							*///
///*	***************************************************************************************************************************************	*///
///*	版		本		：		1.0																																				*///
///*	作		者		：		CL																																					*///
///*	日		期		：		2012/04/09																																	*///
///*	****************************************************************************************************************************************	*///
//////////////////////////////////////////////////////////////////////////
#include <string>

using namespace std;


class Util
{
public:
	static string getExtension(string path);
	static string getDir(string path);
	static string getFileName(string path);
	template <class T>
	static string toString(T value);
	static string double2String(double value);

	////From VpCore
	static wstring Ansi2WChar(LPCSTR pszSrc, int nLen);
	static string WChar2Ansi(LPCWSTR pwszSrc);
	static string itos( int );
	//static bool folderExist(const string &strPath);
	//static int GetFileCount(string strPath , string filter);
};
